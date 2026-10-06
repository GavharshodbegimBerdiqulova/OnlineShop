from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Address
from .validators import email_validator, login_type, normalize_phone, phone_validator, username_validator

User = get_user_model()


class SendTestEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    subject = serializers.CharField(max_length=200, default="OnlineShop test")
    message = serializers.CharField(default="Gmail orqali yuborish ishlayapti.")


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.CharField(validators=[email_validator])
    username = serializers.CharField(validators=[username_validator])
    phone = serializers.CharField(validators=[phone_validator])
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    password2 = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ("email", "username", "phone", "first_name", "last_name", "password", "password2")

    def to_internal_value(self, data):
        if data.get("phone"):
            data = data.copy()
            data["phone"] = normalize_phone(data["phone"])
        return super().to_internal_value(data)

    def validate_email(self, value):
        value = value.lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Bu email allaqachon ro'yxatdan o'tgan")
        return value

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Bu username band")
        return value

    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Bu telefon raqam allaqachon ro'yxatdan o'tgan")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password2": "Parollar bir xil emas"})
        validate_password(attrs["password"])
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(min_length=6, max_length=6)


class LoginSerializer(serializers.Serializer):
    login = serializers.CharField(help_text="Email, telefon (+998901234567) yoki username")
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)

    def validate(self, attrs):
        login = attrs["login"].strip()
        kind = login_type(login)
        if kind is None:
            raise serializers.ValidationError({"login": "Email, telefon yoki username noto'g'ri formatda"})

        if kind == "email":
            user = User.objects.filter(email__iexact=login).first()
        elif kind == "phone":
            user = User.objects.filter(phone=normalize_phone(login)).first()
        else:
            user = User.objects.filter(username__iexact=login).first()

        if user is None or not user.check_password(attrs["password"]) or not user.is_active:
            raise serializers.ValidationError({"detail": "Login yoki parol noto'g'ri"})
        if not user.is_verified:
            raise serializers.ValidationError({"detail": "Email tasdiqlanmagan"})

        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": ProfileSerializer(user).data,
        }


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(min_length=6, max_length=6)
    new_password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate_new_password(self, value):
        validate_password(value)
        return value


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, style={"input_type": "password"})
    new_password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate_old_password(self, value):
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError("Eski parol noto'g'ri")
        return value

    def validate_new_password(self, value):
        validate_password(value)
        return value


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "username", "first_name", "last_name", "phone", "avatar", "birth_date", "role", "is_verified")
        read_only_fields = ("id", "email", "role", "is_verified")

    def to_internal_value(self, data):
        if data.get("phone"):
            data = data.copy()
            data["phone"] = normalize_phone(data["phone"])
        return super().to_internal_value(data)


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ("id", "title", "city", "street", "zip_code", "is_default")
