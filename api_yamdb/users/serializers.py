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
