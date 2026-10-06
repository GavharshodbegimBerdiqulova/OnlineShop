from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Address, VerificationCode
from .serializers import (
    AddressSerializer,
    AvatarSerializer,
    ChangePasswordSerializer,
    LoginSerializer,
    LogoutSerializer,
    ProfileSerializer,
    ResetPasswordSerializer,
    SendCodeSerializer,
    SendTestEmailSerializer,
    SignUpSerializer,
    TokenResponseSerializer,
    VerifyCodeSerializer,
)
from .services.code_service import check_code, make_token, read_token, send_code
from .services.email_service import send_email
from .services.token_service import get_tokens

User = get_user_model()


class SendCodeView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=SendCodeSerializer,
        responses={200: None},
        tags=["auth"],
        summary="1. Email yoki telefonga tasdiqlash kodi yuborish",
    )
    def post(self, request):
        serializer = SendCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if data["purpose"] == VerificationCode.Purpose.SIGNUP or data["user_exists"]:
            send_code(data["contact"], data["purpose"])
        return Response({"detail": "Tasdiqlash kodi yuborildi", "resend_after": 120})


class VerifyCodeView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=VerifyCodeSerializer,
        responses={200: TokenResponseSerializer},
        tags=["auth"],
        summary="2. Kodni tasdiqlash (sign-up yoki reset-password uchun token qaytaradi)",
    )
    def post(self, request):
        serializer = VerifyCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if not check_code(data["contact"], data["code"], data["purpose"]):
            return Response({"detail": "Kod noto'g'ri yoki muddati o'tgan"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"token": make_token(data["contact"], data["purpose"])})


class SignUpView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=SignUpSerializer,
        responses={201: None},
        tags=["auth"],
        summary="3. Ism va parol kiritib, foydalanuvchi yaratish",
    )
    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        data = get_tokens(user)
        data["user"] = ProfileSerializer(user, context={"request": request}).data
        return Response(data, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    @extend_schema(tags=["auth"], summary="5. Kirish (email, telefon yoki username bilan)")
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


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


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=ResetPasswordSerializer,
        responses={200: None},
        tags=["auth"],
        summary="Parolni tiklash (verify-code tokeni bilan)",
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        contact = read_token(data["token"], VerificationCode.Purpose.RESET)
        if contact is None:
            return Response({"detail": "Token noto'g'ri yoki muddati o'tgan"}, status=status.HTTP_400_BAD_REQUEST)
        if "@" in contact:
            user = User.objects.filter(email__iexact=contact).first()
        else:
            user = User.objects.filter(phone=contact).first()
        if user is None:
            return Response({"detail": "Foydalanuvchi topilmadi"}, status=status.HTTP_400_BAD_REQUEST)
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


class AvatarView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request=AvatarSerializer,
        responses={200: ProfileSerializer},
        tags=["profile"],
        summary="4. Profil rasmini yuklash (ixtiyoriy)",
    )
    def post(self, request):
        serializer = AvatarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if request.user.avatar:
            request.user.avatar.delete(save=False)
        request.user.avatar = serializer.validated_data["avatar"]
        request.user.save()
        return Response(ProfileSerializer(request.user, context={"request": request}).data)

    @extend_schema(responses={204: None}, tags=["profile"], summary="Profil rasmini o'chirish")
    def delete(self, request):
        if request.user.avatar:
            request.user.avatar.delete(save=False)
            request.user.avatar = None
            request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


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
