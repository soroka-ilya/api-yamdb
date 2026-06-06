from django.contrib.auth import get_user_model
from django.contrib.auth.validators import UnicodeUsernameValidator
from rest_framework import serializers

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

        if (
            User.objects.filter(username=username)
            .exclude(email=email)
            .exists()
        ):
            raise serializers.ValidationError(
                {'username': 'This username is already taken.'}
            )
        
        if (
            User.objects.filter(email=email)
            .exclude(username=username)
            .exists()
        ):
            raise serializers.ValidationError(
                {'email': 'This email is already taken.'}
            )
    
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
