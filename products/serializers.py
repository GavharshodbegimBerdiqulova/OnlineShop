from rest_framework import serializers

from .models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(required=False)

    class Meta:
        model = Category
        fields = ("id", "name", "slug")


class ProductSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(required=False)
    category_name = serializers.CharField(source="category.name", read_only=True)
    is_active = serializers.BooleanField(default=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "category",
            "category_name",
            "name",
            "slug",
            "description",
            "price",
            "stock",
            "image",
            "is_active",
            "created_at",
        )
        read_only_fields = ("created_at",)

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Narx 0 dan katta bo'lishi kerak")
        return value
