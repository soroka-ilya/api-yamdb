from django.contrib.auth import get_user_model
from django.contrib.auth.validators import UnicodeUsernameValidator
from rest_framework import serializers

from reviews.models import Category, Comment, Genre, Review, Title

User = get_user_model()
username_validator = UnicodeUsernameValidator()


class UsernameValidateMixin:
    """Миксин для валидации имени пользователя."""

    def validate_username(self, username):
        if username.lower() == 'me':
            raise serializers.ValidationError(
                'Имя пользователя "me" запрещено.'
            )
        return username


class BaseUsernameSerializer(UsernameValidateMixin, serializers.Serializer):
    """Базовый сериализатор для полей авторизации с общим полем username."""

    username = serializers.CharField(
        max_length=150,
        validators=[username_validator],
    )


class SignupSerializer(BaseUsernameSerializer):
    """Сериализатор регистрации пользователя."""

    email = serializers.EmailField(max_length=254)

    def validate(self, data):
        username = data.get('username')
        email = data.get('email')
        errors = {}

        if (User.objects.filter(username=username)
                .exclude(email=email).exists()):
            errors['username'] = 'Этот username уже занят.'

        if (User.objects.filter(email=email)
                .exclude(username=username).exists()):
            errors['email'] = 'Этот email уже занят.'

        if errors:
            raise serializers.ValidationError(errors)

        return data


class TokenSerializer(BaseUsernameSerializer):
    """Сериализатор получения JWT-токена."""

    confirmation_code = serializers.CharField(write_only=True)


class UserSerializer(UsernameValidateMixin, serializers.ModelSerializer):
    """Сериализатор для работы с моделью User администратором."""

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'bio',
            'role',
        )

    def validate(self, data):
        username = data.get('username')
        email = data.get('email')

        if username and User.objects.filter(username=username).exclude(
            pk=getattr(self.instance, 'pk', None)
        ).exists():
            raise serializers.ValidationError(
                {'username': 'Этот username уже занят.'}
            )

        if email and User.objects.filter(email=email).exclude(
            pk=getattr(self.instance, 'pk', None)
        ).exists():
            raise serializers.ValidationError(
                {'email': 'Этот email уже зарегистрирован.'}
            )

        return data


class MeSerializer(UserSerializer):
    """Сериализатор для работы пользователя со своим профилем."""

    class Meta(UserSerializer.Meta):
        read_only_fields = ('role',)


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор категорий."""

    class Meta:
        model = Category
        fields = ('name', 'slug')


class GenreSerializer(serializers.ModelSerializer):
    """Сериализатор жанров."""

    class Meta:
        model = Genre
        fields = ('name', 'slug')


class TitleReadSerializer(serializers.ModelSerializer):
    """Сериализатор для безопасного чтения произведений."""

    category = CategorySerializer(read_only=True)
    genre = GenreSerializer(many=True, read_only=True)
    rating = serializers.IntegerField(read_only=True)

    class Meta:
        model = Title
        fields = (
            'id', 'name', 'year', 'rating',
            'description', 'genre', 'category'
        )


class TitleWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для записи и изменения произведений."""

    genre = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Genre.objects.all(),
        many=True,
        allow_empty=False,
    )
    category = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Category.objects.all(),
    )

    class Meta:
        model = Title
        fields = ('id', 'name', 'year', 'description', 'genre', 'category')


class ReviewSerializer(serializers.ModelSerializer):
    """Сериализатор отзывов."""

    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    class Meta:
        model = Review
        fields = ('id', 'text', 'author', 'score', 'pub_date')

    def validate(self, data):
        request = self.context.get('request')
        if request and request.method == 'POST':
            view = self.context.get('view')
            title_id = view.kwargs.get('title_id')
            if request.user.reviews.filter(title_id=title_id).exists():
                raise serializers.ValidationError(
                    'Вы уже оставили отзыв на это произведение'
                )
        return data


class CommentSerializer(serializers.ModelSerializer):
    """Сериализатор комментариев."""

    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    class Meta:
        model = Comment
        fields = ('id', 'text', 'author', 'pub_date')
