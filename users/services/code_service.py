from django.core import signing
from django.utils import timezone
from rest_framework.exceptions import Throttled

from users.exceptions import SendCodeError
from users.models import VerificationCode
from users.validators import login_type, normalize_phone

from .email_service import send_email
from .sms_service import send_sms

RESEND_SECONDS = 120
MAX_ATTEMPTS = 5
TOKEN_MAX_AGE = 15 * 60
TOKEN_SALT = "users.contact-token"


def normalize_contact(contact):
    contact = contact.strip()
    kind = login_type(contact)
    if kind == "email":
        return contact.lower(), "email"
    if kind == "phone":
        return normalize_phone(contact), "phone"
    return None, None


def send_code(contact, purpose):
    last = VerificationCode.objects.filter(contact=contact, purpose=purpose).order_by("-created_at").first()
    if last:
        passed = (timezone.now() - last.created_at).total_seconds()
        if passed < RESEND_SECONDS:
            wait = int(RESEND_SECONDS - passed) + 1
            raise Throttled(wait=wait, detail=f"Kodni {wait} soniyadan keyin qayta yuborish mumkin")

    VerificationCode.objects.filter(contact=contact, purpose=purpose, is_used=False).update(is_used=True)
    verification = VerificationCode.objects.create(
        contact=contact,
        purpose=purpose,
        code=VerificationCode.generate_code(),
    )

    text = f"OnlineShop tasdiqlash kodi: {verification.code}. Kod 5 daqiqa amal qiladi."
    try:
        if "@" in contact:
            send_email(contact, "Tasdiqlash kodi", text)
        else:
            send_sms(contact, text)
    except Exception:
        verification.delete()
        raise SendCodeError()
    return verification


def check_code(contact, code, purpose):
    verification = (
        VerificationCode.objects.filter(contact=contact, purpose=purpose, is_used=False)
        .order_by("-created_at")
        .first()
    )
    if verification is None or verification.is_expired() or verification.attempts >= MAX_ATTEMPTS:
        return False
    if verification.code != code:
        verification.attempts += 1
        verification.save(update_fields=["attempts"])
        return False
    verification.is_used = True
    verification.save(update_fields=["is_used"])
    return True


def make_token(contact, purpose):
    return signing.dumps({"contact": contact, "purpose": purpose}, salt=TOKEN_SALT)


def read_token(token, purpose):
    try:
        data = signing.loads(token, salt=TOKEN_SALT, max_age=TOKEN_MAX_AGE)
    except signing.BadSignature:
        return None
    if data.get("purpose") != purpose:
        return None
    return data["contact"]
