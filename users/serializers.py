from rest_framework import serializers


class SendTestEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    subject = serializers.CharField(max_length=200, default="OnlineShop test")
    message = serializers.CharField(default="Gmail orqali yuborish ishlayapti.")
