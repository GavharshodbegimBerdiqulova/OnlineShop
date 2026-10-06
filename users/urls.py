from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    AddressViewSet,
    AvatarView,
    ChangePasswordView,
    LoginView,
    LogoutView,
    ProfileView,
    ResetPasswordView,
    SendCodeView,
    SendTestEmailView,
    SignUpView,
    VerifyCodeView,
)

router = DefaultRouter()
router.register('addresses', AddressViewSet, basename='address')

urlpatterns = [
    path('auth/send-code/', SendCodeView.as_view(), name='send-code'),
    path('auth/verify-code/', VerifyCodeView.as_view(), name='verify-code'),
    path('auth/sign-up/', SignUpView.as_view(), name='sign-up'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('auth/me/', ProfileView.as_view(), name='me'),
    path('auth/me/avatar/', AvatarView.as_view(), name='avatar'),
    path('send-test-email/', SendTestEmailView.as_view(), name='send-test-email'),
    path('', include(router.urls)),
]
