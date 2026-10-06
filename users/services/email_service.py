from django.conf import settings
from django.core.mail import send_mail

from users.models import VerificationCode


def send_email(to_email, subject, message):
    return send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to_email],
        fail_silently=False,
    )


def create_code(user, purpose):
    VerificationCode.objects.filter(user=user, purpose=purpose, is_used=False).update(is_used=True)
    return VerificationCode.objects.create(
        user=user,
        purpose=purpose,
        code=VerificationCode.generate_code(),
    )


def send_verification_code(user):
    code = create_code(user, VerificationCode.Purpose.EMAIL)
    send_email(
        user.email,
        "Emailni tasdiqlash",
        f"Sizning tasdiqlash kodingiz: {code.code}\nKod 5 daqiqa amal qiladi.",
    )
    return code


def send_reset_code(user):
    code = create_code(user, VerificationCode.Purpose.RESET)
    send_email(
        user.email,
        "Parolni tiklash",
        f"Parolni tiklash kodi: {code.code}\nKod 5 daqiqa amal qiladi.",
    )
    return code


def verify_code(user, code, purpose):
    verification = VerificationCode.objects.filter(
        user=user, code=code, purpose=purpose, is_used=False
    ).last()
    if verification is None or verification.is_expired():
        return False
    verification.is_used = True
    verification.save()
    return True
