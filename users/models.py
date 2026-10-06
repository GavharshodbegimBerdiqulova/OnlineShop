import secrets
from datetime import timedelta

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone

from .validators import email_validator, phone_validator, username_validator


class UserManager(BaseUserManager):

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email and not extra_fields.get("phone"):
            raise ValueError("Email yoki telefon kiritilishi shart")
        email = self.normalize_email(email) if email else None
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Admin uchun email kiritilishi shart")
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_verified", True)
        extra_fields.setdefault("role", User.Role.ADMIN)
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = "customer", "Mijoz"
        ADMIN = "admin", "Admin"

    username = models.CharField("Username", max_length=20, unique=True, null=True, blank=True, validators=[username_validator])
    email = models.EmailField("Email", unique=True, null=True, blank=True, validators=[email_validator])
    phone = models.CharField("Telefon", max_length=13, unique=True, null=True, blank=True, validators=[phone_validator])
    avatar = models.ImageField("Rasm", upload_to="avatars/", blank=True, null=True)
    birth_date = models.DateField("Tug'ilgan sana", blank=True, null=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.CUSTOMER)
    is_verified = models.BooleanField("Kontakt tasdiqlangan", default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"

    def __str__(self):
        return self.email or self.phone or f"User #{self.pk}"

    @property
    def full_name(self):
        return self.get_full_name() or str(self)


class Address(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    title = models.CharField("Nomi", max_length=50, help_text="Masalan: Uy, Ish")
    city = models.CharField("Shahar", max_length=100)
    street = models.CharField("Ko'cha", max_length=255)
    zip_code = models.CharField("Indeks", max_length=10, blank=True)
    is_default = models.BooleanField("Asosiy manzil", default=False)

    class Meta:
        verbose_name = "Manzil"
        verbose_name_plural = "Manzillar"

    def __str__(self):
        return f"{self.title}: {self.city}, {self.street}"

    def save(self, *args, **kwargs):
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class VerificationCode(models.Model):
    class Purpose(models.TextChoices):
        SIGNUP = "signup", "Ro'yxatdan o'tish"
        RESET = "reset", "Parolni tiklash"

    contact = models.CharField("Email yoki telefon", max_length=255, db_index=True)
    code = models.CharField(max_length=4)
    purpose = models.CharField(max_length=10, choices=Purpose.choices)
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Tasdiqlash kodi"
        verbose_name_plural = "Tasdiqlash kodlari"

    def __str__(self):
        return f"{self.contact} - {self.purpose}"

    @staticmethod
    def generate_code():
        return f"{secrets.randbelow(10000):04d}"

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)
