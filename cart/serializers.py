from rest_framework import serializers

from products.models import Product

from .models import Cart, CartItem


class CartProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ("id", "name", "slug", "price", "image", "stock")


class CartItemSerializer(serializers.ModelSerializer):
    product = CartProductSerializer(read_only=True)
    subtotal = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ("id", "product", "quantity", "subtotal")


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ("id", "items", "total_price")


class AddToCartSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True))
    quantity = serializers.IntegerField(min_value=1, default=1)

    def validate(self, attrs):
        cart = self.context["cart"]
        product = attrs["product"]
        item = cart.items.filter(product=product).first()
        total = attrs["quantity"] + (item.quantity if item else 0)
        if total > product.stock:
            raise serializers.ValidationError({"quantity": f"Omborda faqat {product.stock} ta mavjud"})
        return attrs


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)

    def validate_quantity(self, value):
        stock = self.context["item"].product.stock
        if value > stock:
            raise serializers.ValidationError(f"Omborda faqat {stock} ta mavjud")
        return value
