from rest_framework.exceptions import APIException


class SendCodeError(APIException):
    status_code = 503
    default_detail = "Kod yuborib bo'lmadi, keyinroq urinib ko'ring"
    default_code = "send_code_failed"
