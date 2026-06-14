from django.contrib.auth import get_user_model
from django.contrib.auth.validators import UnicodeUsernameValidator
from rest_framework import serializers
from django.db.models import Avg
from . import models


User = get_user_model()
username_validator = UnicodeUsernameValidator()


class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField(
        max_length=254,
        required=True,
    )
    username = serializers.CharField(
        max_length=150,
        required=True,
        validators=[username_validator],
    )

    def validate_username(self, value):
        if value.lower() == 'me':
            raise serializers.ValidationError(
                'Username "me" is not allowed.'
            )
        return value

    def validate(self, data):
        username = data.get('username')
        email = data.get('email')
        errors = {}

        if (
            User.objects.filter(username=username)
            .exclude(email=email)
            .exists()
        ):
            errors['username'] = 'This username is already taken.'

        if (
            User.objects.filter(email=email)
            .exclude(username=username)
            .exists()
        ):
            errors['email'] = 'This email is already taken.'

        if errors:
            raise serializers.ValidationError(errors)

        return data


class TokenSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=150,
        required=True,
        validators=[username_validator],
    )
    confirmation_code = serializers.CharField(
        required=True,
        write_only=True,
    )


class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        max_length=150,
        required=True,
        validators=[username_validator],
    )
    email = serializers.EmailField(
        max_length=254,
        required=True,
    )

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

    def validate_username(self, value):
        if value.lower() == 'me':
            raise serializers.ValidationError(
                'Username "me" is not allowed.'
            )
        return value

    def validate(self, data):
        username = data.get('username')
        email = data.get('email')

        if username and (
            User.objects.filter(username=username)
            .exclude(pk=getattr(self.instance, 'pk', None))
            .exists()
        ):
            raise serializers.ValidationError(
                {'username': 'This username is already taken.'}
            )

        if email and (
            User.objects.filter(email=email)
            .exclude(pk=getattr(self.instance, 'pk', None))
            .exists()
        ):
            raise serializers.ValidationError(
                {'email': 'This email is already registered.'}
            )

        return data


class MeSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        read_only_fields = ('role',)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Category
        fields = ('name', 'slug')


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Genre
        fields = ('name', 'slug')


class TitleReadSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    genre = GenreSerializer(many=True)
    rating = serializers.SerializerMethodField()

    class Meta:
        model = models.Title
        fields = ('id', 'name', 'year', 'rating',
                  'description', 'genre', 'category')

    def get_rating(self, obj):
        try:
            reviews = getattr(obj, 'reviews', None)
            if reviews is None:
                reviews = getattr(obj, 'review_set', None)
            if reviews is None:
                return None
            agg = reviews.aggregate(avg=Avg('score'))
            avg = agg.get('avg')
            return round(avg) if avg is not None else None
        except Exception:
            return None


class TitleWriteSerializer(serializers.ModelSerializer):
    genre = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=models.Genre.objects.all(),
        many=True,
    )
    category = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=models.Category.objects.all(),
    )

    class Meta:
        model = models.Title
        fields = ('id', 'name', 'year', 'description', 'genre', 'category')

    def validate_name(self, value):
        if len(value) > 256:
            raise serializers.ValidationError(
                'The field `name` must be at most 256 characters.'
            )
        return value

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.fields['genre'].queryset = models.Genre.objects.all()
            self.fields['category'].queryset = models.Category.objects.all()
        except Exception:
            pass
