from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import make_password

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "role"]
        extra_kwargs = {
            "password": {"write_only": True},  # Prevent returning password in response
        }

    def create(self, validated_data):
        """
        Create and return a new user instance with a properly hashed password.
        """
        password = validated_data.pop("password")  # Remove password from validated data
        user = User(**validated_data)  # Create a user instance
        user.set_password(password)  # Hash the password correctly
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        """
        Validate the login credentials.
        """
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            raise serializers.ValidationError("Both username and password are required.")

        return data

class TokenSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()

    @staticmethod
    def get_tokens_for_user(user):
        """
        Generate JWT tokens for a given user.
        """
        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }