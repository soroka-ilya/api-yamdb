from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404

from rest_framework import filters, status, viewsets, mixins
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken

from .models import Title, Category, Genre
from reviews.models import Review
from .permissions import IsAdmin, IsAdminOrReadOnly, IsAuthorModeratorAdmin
from .serializers import (
    MeSerializer, SignupSerializer, TokenSerializer, UserSerializer,
    CategorySerializer, GenreSerializer,
    TitleReadSerializer, TitleWriteSerializer,
    ReviewSerializer, CommentSerializer
)

User = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    serializer = SignupSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user, created = User.objects.get_or_create(
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
        return Response(
            {'confirmation_code': 'Invalid confirmation code.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    token = AccessToken.for_user(user)

    return Response(
        {'token': str(token)},
        status=status.HTTP_200_OK,
    )


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAdmin,)
    lookup_field = 'username'
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    @action(
        detail=False,
        methods=['get', 'patch'],
        permission_classes=(IsAuthenticated,),
        url_path='me',
    )
    def me(self, request):
        serializer = MeSerializer(
            request.user,
            data=request.data,
            partial=True,
        )

        if request.method == 'GET':
            serializer = MeSerializer(request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class CategoryViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (IsAdminOrReadOnly,)
    lookup_field = 'slug'
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    http_method_names = ['get', 'post', 'delete', 'head', 'options']


class GenreViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = (IsAdminOrReadOnly,)
    lookup_field = 'slug'
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    http_method_names = ['get', 'post', 'delete', 'head', 'options']


class TitleViewSet(ModelViewSet):
    queryset = Title.objects.all().select_related(
        'category').prefetch_related('genre')
    permission_classes = (IsAdminOrReadOnly,)
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return TitleReadSerializer
        return TitleWriteSerializer

    def get_queryset(self):
        qs = self.queryset
        genre = self.request.query_params.get('genre')
        category = self.request.query_params.get('category')
        year = self.request.query_params.get('year')
        name = self.request.query_params.get('name')
        if genre:
            qs = qs.filter(genre__slug=genre)
        if category:
            qs = qs.filter(category__slug=category)
        if year:
            qs = qs.filter(year=year)
        if name:
            qs = qs.filter(name__icontains=name)
        return qs


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = (IsAuthorModeratorAdmin,)
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_title(self):
        return get_object_or_404(Title, id=self.kwargs.get('title_id'))

    def get_queryset(self):
        return self.get_title().reviews.all()

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
            title=self.get_title()
        )


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = (IsAuthorModeratorAdmin,)
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

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
