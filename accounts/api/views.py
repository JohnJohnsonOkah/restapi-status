from django.contrib.auth import authenticate, get_user_model, login, logout
from django.db.models import Q
from django.shortcuts import redirect

from rest_framework import permissions, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_jwt.settings import api_settings

from .permissions import AnonPermissionOnly
from .serializers import UserRegisterSerializer, UserAuthSerializer


jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
jwt_response_payload_handler = api_settings.JWT_RESPONSE_PAYLOAD_HANDLER


User = get_user_model()


# simple logout view
def logout_view(request):
    logout(request)
    return redirect("api-auth:auth")


# Customized Authentication View
class AuthView(APIView):
    permission_classes = [AnonPermissionOnly]
    serializer_class = UserAuthSerializer

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return Response({'detail': 'You are already authenticated'},
                            status=400)
        data = request.data
        username = data.get('username')  # username or email address
        password = data.get('password')
        # user = authenticate(username=username, password=password)

        # allow to accept username or email
        qs = User.objects.filter(
            Q(username__iexact=username) |
            Q(email__iexact=username)
        ).distinct()
        if qs.count() == 1:
            user_obj = qs.first()
            if user_obj.check_password(password):
                user = user_obj
                login(request, user)  # login in the user
            else:
                return Response({"detail": "Invalid password"}, status=401)
            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)
            response = jwt_response_payload_handler(
                token, user, request=request)
            return Response(response)
        return Response({"detail": "User does not exist"}, status=401)


class RegisterAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [AnonPermissionOnly]

    def get_serializer_context(self, *args, **kwargs):
        return {"request": self.request}
