from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    UserViewSet, get_token, signup,
    CategoryViewSet, GenreViewSet, TitleViewSet,
)

router_v1 = DefaultRouter()
router_v1.register(
    'users',
    UserViewSet,
    basename='users',
)
router_v1.register(
    'categories',
    CategoryViewSet,
    basename='categories',
)
router_v1.register(
    'genres',
    GenreViewSet,
    basename='genres',
)
router_v1.register(
    'titles',
    TitleViewSet,
    basename='titles',
)

router.register(
    r'titles/(?P<title_id>\d+)/reviews',
    ReviewViewSet,
    basename='reviews'
)
router.register(
    r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
    CommentViewSet,
    basename='comments'
)

urlpatterns = [
    path('auth/signup/', signup, name='signup'),
    path('auth/token/', get_token, name='token'),
    path('', include(router_v1.urls)),
]
