from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken

from reviews.models import Category, Genre, Review, Title
from .permissions import IsAdmin, IsAdminOrReadOnly, IsAuthorModeratorAdmin
from .serializers import (
    CategorySerializer,
    CommentSerializer,
    GenreSerializer,
    MeSerializer,
    ReviewSerializer,
    SignupSerializer,
    TitleReadSerializer,
    TitleWriteSerializer,
    TokenSerializer,
    UserSerializer,
)

User = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    """Регистрация нового пользователя и отправка кода подтверждения."""
    serializer = SignupSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user, _ = User.objects.get_or_create(
        username=serializer.validated_data['username'],
        email=serializer.validated_data['email'],
    )

    confirmation_code = default_token_generator.make_token(user)
    user.confirmation_code = confirmation_code
    user.save()

    send_mail(
        'YaMDb confirmation code',
        f'Your confirmation code: {confirmation_code}',
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def get_token(request):
    """Получение JWT-токена по коду подтверждения."""
    serializer = TokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = get_object_or_404(
        User,
        username=serializer.validated_data['username'],
    )

    confirmation_code = serializer.validated_data['confirmation_code']
    is_valid_code = (
        user.confirmation_code == confirmation_code
        or default_token_generator.check_token(user, confirmation_code)
    )

    if not is_valid_code:
        raise ValidationError(
            {'confirmation_code': 'Неверный код подтверждения.'}
        )

    token = AccessToken.for_user(user)
    return Response({'token': str(token)}, status=status.HTTP_200_OK)


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет для управления пользователями администратором."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAdmin,)
    lookup_field = 'username'
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)
    http_method_names = ('get', 'post', 'patch', 'delete', 'head', 'options')

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        url_path='me',
    )
    def me(self, request):
        """Получение данных своего профиля."""
        serializer = MeSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @me.mapping.patch
    def update_me(self, request):
        """Редактирование своего профиля."""
        serializer = MeSerializer(
            request.user,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class CategoryGenreBaseViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Базовый вьюсет для категорий и жанров."""

    permission_classes = (IsAdminOrReadOnly,)
    lookup_field = 'slug'
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    http_method_names = ('get', 'post', 'delete', 'head', 'options')


class CategoryViewSet(CategoryGenreBaseViewSet):
    """Вьюсет для работы с категориями."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class GenreViewSet(CategoryGenreBaseViewSet):
    """Вьюсет для работы с жанрами."""

    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class TitleViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с произведениями."""

    permission_classes = (IsAdminOrReadOnly,)
    http_method_names = ('get', 'post', 'patch', 'delete', 'head', 'options')

    def get_serializer_class(self):
        if self.action in {'list', 'retrieve'}:
            return TitleReadSerializer
        return TitleWriteSerializer

    def get_queryset(self):
        queryset = Title.objects.select_related(
            'category'
        ).prefetch_related(
            'genre'
        ).annotate(
            rating=Avg('reviews__score')
        ).order_by('name')

        genre = self.request.query_params.get('genre')
        category = self.request.query_params.get('category')
        year = self.request.query_params.get('year')
        name = self.request.query_params.get('name')

        if genre:
            queryset = queryset.filter(genre__slug=genre)
        if category:
            queryset = queryset.filter(category__slug=category)
        if year:
            queryset = queryset.filter(year=year)
        if name:
            queryset = queryset.filter(name__icontains=name)

        return queryset


class ReviewCommentBaseViewSet(viewsets.ModelViewSet):
    """Базовый вьюсет для отзывов и комментариев для соблюдения DRY."""

    permission_classes = (IsAuthorModeratorAdmin,)
    http_method_names = ('get', 'post', 'patch', 'delete', 'head', 'options')


class ReviewViewSet(ReviewCommentBaseViewSet):
    """Вьюсет для работы с отзывами."""

    serializer_class = ReviewSerializer

    def get_title(self):
        return get_object_or_404(Title, id=self.kwargs.get('title_id'))

    def get_queryset(self):
        return self.get_title().reviews.all()

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
            title=self.get_title()
        )


class CommentViewSet(ReviewCommentBaseViewSet):
    """Вьюсет для работы с комментариями."""

    serializer_class = CommentSerializer

    def get_review(self):
        return get_object_or_404(
            Review,
            id=self.kwargs.get('review_id'),
            title_id=self.kwargs.get('title_id')
        )

    def get_queryset(self):
        return self.get_review().comments.all()

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
            review=self.get_review()
        )
