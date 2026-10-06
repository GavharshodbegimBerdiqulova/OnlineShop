from django.conf import settings


def send_sms(phone, message):
    if settings.SMS_BACKEND == "console":
        print(f"[SMS] {phone}: {message}")
        return True
    raise NotImplementedError(f"SMS backend yozilmagan: {settings.SMS_BACKEND}")
