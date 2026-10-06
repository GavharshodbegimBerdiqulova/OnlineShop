from datetime import timedelta

from rest_framework_simplejwt.tokens import RefreshToken


def get_tokens(user, remember_me=False):
    refresh = RefreshToken.for_user(user)
    refresh.set_exp(lifetime=timedelta(days=30 if remember_me else 1))
    return {"access": str(refresh.access_token), "refresh": str(refresh)}
