from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Address, VerificationCode
from .services.code_service import normalize_contact, read_token
from .services.token_service import get_tokens
from .validators import login_type, normalize_phone, username_validator

User = get_user_model()

CONTACT_HELP = "Email yoki telefon (+998901234567)"


def find_user_by_contact(contact):
    if "@" in contact:
        return User.objects.filter(email__iexact=contact).first()
    return User.objects.filter(phone=contact).first()


class SendTestEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    subject = serializers.CharField(max_length=200, default="OnlineShop test")
    message = serializers.CharField(default="Gmail orqali yuborish ishlayapti.")


class ContactField(serializers.CharField):
    def __init__(self, **kwargs):
        kwargs.setdefault("help_text", CONTACT_HELP)
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        contact, kind = normalize_contact(value)
        if contact is None:
            raise serializers.ValidationError("Email yoki telefon (+998XXXXXXXXX) noto'g'ri formatda")
        return contact


class SendCodeSerializer(serializers.Serializer):
    contact = ContactField()
    purpose = serializers.ChoiceField(choices=VerificationCode.Purpose.choices)

    def validate(self, attrs):
        user = find_user_by_contact(attrs["contact"])
        attrs["user_exists"] = user is not None
        if attrs["purpose"] == VerificationCode.Purpose.SIGNUP and user is not None:
            raise serializers.ValidationError({"contact": "Bu email yoki telefon allaqachon ro'yxatdan o'tgan"})
        return attrs


class VerifyCodeSerializer(serializers.Serializer):
    contact = ContactField()
    purpose = serializers.ChoiceField(choices=VerificationCode.Purpose.choices)
    code = serializers.RegexField(r"^\d{4}$", error_messages={"invalid": "Kod 4 ta raqamdan iborat bo'lishi kerak"})


class TokenResponseSerializer(serializers.Serializer):
    token = serializers.CharField()


class SignUpSerializer(serializers.Serializer):
    token = serializers.CharField(help_text="verify-code javobidagi token")
    full_name = serializers.CharField(min_length=2, max_length=150)
    username = serializers.CharField(required=False, validators=[username_validator])
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    password2 = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate_full_name(self, value):
        value = " ".join(value.split())
        if len(value) < 2:
            raise serializers.ValidationError("Ism kamida 2 ta belgidan iborat bo'lishi kerak")
        return value

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Bu username band")
        return value

    def validate(self, attrs):
        contact = read_token(attrs["token"], VerificationCode.Purpose.SIGNUP)
        if contact is None:
            raise serializers.ValidationError({"token": "Token noto'g'ri yoki muddati o'tgan"})
        if find_user_by_contact(contact) is not None:
            raise serializers.ValidationError({"token": "Bu email yoki telefon allaqachon ro'yxatdan o'tgan"})
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password2": "Parollar bir xil emas"})
        validate_password(attrs["password"])
        attrs["contact"] = contact
        return attrs

    def create(self, validated_data):
        contact = validated_data["contact"]
        parts = validated_data["full_name"].split(" ", 1)
        extra = {"first_name": parts[0], "last_name": parts[1] if len(parts) > 1 else "", "is_verified": True}
        if validated_data.get("username"):
            extra["username"] = validated_data["username"]
        if "@" in contact:
            email = contact
        else:
            email = None
            extra["phone"] = contact
        return User.objects.create_user(email=email, password=validated_data["password"], **extra)


class LoginSerializer(serializers.Serializer):
    login = serializers.CharField(help_text="Email, telefon (+998901234567) yoki username")
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    remember_me = serializers.BooleanField(default=False, write_only=True)
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
            raise serializers.ValidationError({"detail": "Hisob tasdiqlanmagan"})

        data = get_tokens(user, attrs["remember_me"])
        data["user"] = ProfileSerializer(user).data
        return data


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField(help_text="verify-code (purpose=reset) javobidagi token")
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
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ("id", "full_name", "first_name", "last_name", "username", "email", "phone", "avatar", "birth_date", "role")
        read_only_fields = ("id", "email", "phone", "role")


class AvatarSerializer(serializers.Serializer):
    avatar = serializers.ImageField()

    def validate_avatar(self, value):
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Rasm hajmi 5 MB dan oshmasligi kerak")
        return value


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ("id", "title", "city", "street", "zip_code", "is_default")
