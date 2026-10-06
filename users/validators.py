import re

from django.core.validators import RegexValidator

EMAIL_REGEX = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$"
PHONE_REGEX = r"^\+998\d{9}$"
USERNAME_REGEX = r"^[A-Za-z][A-Za-z0-9_]{2,19}$"

email_validator = RegexValidator(EMAIL_REGEX, "Email noto'g'ri formatda")
phone_validator = RegexValidator(PHONE_REGEX, "Telefon +998901234567 formatida bo'lishi kerak")
username_validator = RegexValidator(
    USERNAME_REGEX,
    "Username harf bilan boshlanishi, 3-20 belgi bo'lishi va faqat harf, raqam va _ dan iborat bo'lishi kerak",
)


def normalize_phone(value):
    value = re.sub(r"[\s\-()]", "", value or "")
    if re.fullmatch(r"998\d{9}", value):
        value = "+" + value
    elif re.fullmatch(r"\d{9}", value):
        value = "+998" + value
    return value


def login_type(value):
    if re.fullmatch(EMAIL_REGEX, value):
        return "email"
    if re.fullmatch(PHONE_REGEX, normalize_phone(value)):
        return "phone"
    if re.fullmatch(USERNAME_REGEX, value):
        return "username"
    return None
