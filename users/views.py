from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import SendTestEmailSerializer
from .services.email_service import send_email


class SendTestEmailView(APIView):
    @extend_schema(request=SendTestEmailSerializer, responses={200: None}, tags=["email"])
    def post(self, request):
        serializer = SendTestEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        print("DATA: ", data)
        try:
            print("Sending...")
            send_email(data["email"], data["subject"], data["message"])
        except Exception as error:
            return Response({"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"detail": "Xat yuborildi"})
