from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status, viewsets
from rest_framework.exceptions import APIException
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Address, VerificationCode
from .serializers import (
    AddressSerializer,
    ChangePasswordSerializer,
    EmailSerializer,
    LoginSerializer,
    LogoutSerializer,
    ProfileSerializer,
    RegisterSerializer,
    ResetPasswordSerializer,
    SendTestEmailSerializer,
    VerifyEmailSerializer,
)
from .services.email_service import send_email, send_reset_code, send_verification_code, verify_code

User = get_user_model()


class EmailSendError(APIException):
    status_code = 503
    default_detail = "Email yuborib bo'lmadi, keyinroq urinib ko'ring"


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    @extend_schema(tags=["auth"], summary="Ro'yxatdan o'tish")
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        try:
            send_verification_code(user)
        except Exception:
            user.delete()
            raise EmailSendError()
        return Response(
            {"detail": "Ro'yxatdan o'tdingiz. Emailga tasdiqlash kodi yuborildi"},
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=VerifyEmailSerializer, responses={200: None}, tags=["auth"], summary="Emailni tasdiqlash")
    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = User.objects.filter(email__iexact=data["email"]).first()
        if user is None or not verify_code(user, data["code"], VerificationCode.Purpose.EMAIL):
            return Response({"detail": "Kod noto'g'ri yoki muddati o'tgan"}, status=status.HTTP_400_BAD_REQUEST)
        user.is_verified = True
        user.save()
        return Response({"detail": "Email tasdiqlandi"})


class ResendCodeView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=EmailSerializer, responses={200: None}, tags=["auth"], summary="Tasdiqlash kodini qayta yuborish")
    def post(self, request):
        serializer = EmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(email__iexact=serializer.validated_data["email"], is_verified=False).first()
        if user:
            try:
                send_verification_code(user)
            except Exception:
                raise EmailSendError()
        return Response({"detail": "Agar email mavjud bo'lsa, kod yuborildi"})


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer

    @extend_schema(tags=["auth"], summary="Kirish (login)")
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class LogoutView(APIView):
    @extend_schema(request=LogoutSerializer, responses={200: None}, tags=["auth"], summary="Chiqish (logout)")
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            RefreshToken(serializer.validated_data["refresh"]).blacklist()
        except TokenError:
            return Response({"detail": "Token noto'g'ri"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "Tizimdan chiqdingiz"})


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=EmailSerializer, responses={200: None}, tags=["auth"], summary="Parolni tiklash kodini yuborish")
    def post(self, request):
        serializer = EmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(email__iexact=serializer.validated_data["email"], is_active=True).first()
        if user:
            try:
                send_reset_code(user)
            except Exception:
                raise EmailSendError()
        return Response({"detail": "Agar email mavjud bo'lsa, kod yuborildi"})


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=ResetPasswordSerializer, responses={200: None}, tags=["auth"], summary="Kod bilan yangi parol o'rnatish")
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = User.objects.filter(email__iexact=data["email"]).first()
        if user is None or not verify_code(user, data["code"], VerificationCode.Purpose.RESET):
            return Response({"detail": "Kod noto'g'ri yoki muddati o'tgan"}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(data["new_password"])
        user.save()
        return Response({"detail": "Parol o'zgartirildi"})


class ChangePasswordView(APIView):
    @extend_schema(request=ChangePasswordSerializer, responses={200: None}, tags=["auth"], summary="Parolni almashtirish")
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return Response({"detail": "Parol o'zgartirildi"})


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    http_method_names = ["get", "patch", "put"]

    def get_object(self):
        return self.request.user

    @extend_schema(tags=["profile"], summary="Profilni ko'rish")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["profile"], summary="Profilni to'liq o'zgartirish")
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(tags=["profile"], summary="Profilni qisman o'zgartirish")
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


@extend_schema(tags=["addresses"])
class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Address.objects.none()
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SendTestEmailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=SendTestEmailSerializer, responses={200: None}, tags=["email"], summary="Email yuborishni sinash")
    def post(self, request):
        serializer = SendTestEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            send_email(data["email"], data["subject"], data["message"])
        except Exception as error:
            return Response({"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"detail": "Xat yuborildi"})
