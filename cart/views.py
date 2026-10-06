from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Cart, CartItem
from .serializers import AddToCartSerializer, CartSerializer, UpdateCartItemSerializer


def get_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def cart_response(cart, code=status.HTTP_200_OK):
    cart = Cart.objects.prefetch_related("items__product").get(pk=cart.pk)
    return Response(CartSerializer(cart).data, status=code)


@extend_schema(tags=["cart"])
class CartView(APIView):
    @extend_schema(responses=CartSerializer, summary="Savatni ko'rish")
    def get(self, request):
        return cart_response(get_cart(request.user))

    @extend_schema(responses=CartSerializer, summary="Savatni tozalash")
    def delete(self, request):
        cart = get_cart(request.user)
        cart.items.all().delete()
        return cart_response(cart)


@extend_schema(tags=["cart"])
class CartItemCreateView(APIView):
    @extend_schema(request=AddToCartSerializer, responses=CartSerializer, summary="Savatga mahsulot qo'shish")
    def post(self, request):
        cart = get_cart(request.user)
        serializer = AddToCartSerializer(data=request.data, context={"cart": cart})
        serializer.is_valid(raise_exception=True)
        product = serializer.validated_data["product"]
        quantity = serializer.validated_data["quantity"]
        item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={"quantity": quantity})
        if not created:
            item.quantity += quantity
            item.save()
        return cart_response(cart, status.HTTP_201_CREATED)


@extend_schema(tags=["cart"])
class CartItemDetailView(APIView):
    @extend_schema(request=UpdateCartItemSerializer, responses=CartSerializer, summary="Mahsulot sonini o'zgartirish")
    def patch(self, request, pk):
        cart = get_cart(request.user)
        item = get_object_or_404(CartItem.objects.select_related("product"), pk=pk, cart=cart)
        serializer = UpdateCartItemSerializer(data=request.data, context={"item": item})
        serializer.is_valid(raise_exception=True)
        item.quantity = serializer.validated_data["quantity"]
        item.save()
        return cart_response(cart)

    @extend_schema(responses=CartSerializer, summary="Mahsulotni savatdan olib tashlash")
    def delete(self, request, pk):
        cart = get_cart(request.user)
        get_object_or_404(CartItem, pk=pk, cart=cart).delete()
        return cart_response(cart)
