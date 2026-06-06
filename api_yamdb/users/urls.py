from django.urls import path

from .views import get_token, signup

urlpatterns = [
    path('auth/signup/', signup, name='signup'),
    path('auth/token/', get_token, name='token'),
]
