import datetime
from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework import serializers
from rest_framework.reverse import reverse as api_reverse
from rest_framework_jwt.settings import api_settings


jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
jwt_response_payload_handler = api_settings.JWT_RESPONSE_PAYLOAD_HANDLER
expire_delta = api_settings.JWT_REFRESH_EXPIRATION_DELTA


User = get_user_model()


# Serializer to show user detail
class UserPublicSerializer(serializers.ModelSerializer):
    uri = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'uri'
        ]

    def get_uri(self, obj):
        request = self.context.get('request')
        return api_reverse('api-user:detail',
                           kwargs={"username": obj.username},
                           request=request)


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        style={'input_type': 'password'},
        write_only=True)  # overide password inbuilt serializer
    password2 = serializers.CharField(
        style={'input_type': 'password'},
        write_only=True)
    token = serializers.SerializerMethodField(read_only=True)
    expires = serializers.SerializerMethodField(read_only=True)
    token_response = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password',
            'password2',
            'token',
            'expires',
            'token_response',
        ]
        extra_kwargs = {'password': {'write_only': True}}

    # custom serializer method -- of field 'token-response'
    def get_token_response(self, obj):
        user = obj
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        response = jwt_response_payload_handler(token, user, request=None)
        return response

    # custom serializer method -- of field 'expires'
    def get_expires(self, obj):
        return timezone.now() + expire_delta - datetime.timedelta(seconds=200)

    # make sure email does not exit in db
    def validate_email(self, value):
        qs = User.objects.filter(email__iexact=value)
        if qs.exists():
            raise serializers.ValidationError(
                "User with this email already exists")
        return value

    # make sure username does not exist in db
    def validate_username(self, value):
        qs = User.objects.filter(username__iexact=value)
        if qs.exists():
            raise serializers.ValidationError(
                "User with this username already exists")
        return value

    # custom serializer method -- of field 'token'
    def get_token(self, obj):
        user = obj
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        return token

    # make sure the two passwords are the same
    def validate(self, data):
        pw = data.get('password')
        pw2 = data.pop('password2')
        if pw != pw2:
            raise serializers.ValidationError("Passwords must match")
        return data

    # create a user with details provided
    def create(self, validate_data):
        user_obj = User(
            username=validate_data.get('username'),
            email=validate_data.get('email'))
        user_obj.set_password(validate_data.get('password'))
        user_obj.save()
        return user_obj


class UserAuthSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        style={'input_type': 'password'},
        write_only=True)  # overide password inbuilt serializer

    class Meta:
        model = User
        fields = [
            'username',
            'password',
        ]
        extra_kwargs = {'password': {'write_only': True}}
