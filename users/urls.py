from django.urls import path

from .views import SendTestEmailView

urlpatterns = [
    path('send-test-email/', SendTestEmailView.as_view(), name='send-test-email'),
]
