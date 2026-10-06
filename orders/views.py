from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from users.permissions import IsAdmin, is_admin

from .models import Order
from .serializers import ChangeStatusSerializer, CreateOrderSerializer, OrderSerializer
from .services import change_status, create_order


@extend_schema(tags=["orders"])
class OrderViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = OrderSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()
        queryset = Order.objects.select_related("address").prefetch_related("items__product")
        if is_admin(self.request.user):
            return queryset
        return queryset.filter(user=self.request.user)

    def get_permissions(self):
        if self.action == "set_status":
            return [IsAdmin()]
        return super().get_permissions()

    @extend_schema(request=CreateOrderSerializer, responses={201: OrderSerializer}, summary="Savatdan buyurtma berish")
    def create(self, request, *args, **kwargs):
        serializer = CreateOrderSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        order = create_order(request.user, serializer.validated_data["address"])
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @extend_schema(request=None, responses=OrderSerializer, summary="Buyurtmani bekor qilish (faqat kutilayotgan)")
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.user_id != request.user.id:
            raise ValidationError({"detail": "Bu buyurtma sizniki emas"})
        if order.status != Order.Status.PENDING:
            raise ValidationError({"detail": "Faqat kutilayotgan buyurtmani bekor qilish mumkin"})
        change_status(order, Order.Status.CANCELED)
        return Response(OrderSerializer(order).data)

    @extend_schema(request=ChangeStatusSerializer, responses=OrderSerializer, summary="Buyurtma holatini o'zgartirish (admin)")
    @action(detail=True, methods=["patch"], url_path="status", url_name="status")
    def set_status(self, request, pk=None):
        order = self.get_object()
        serializer = ChangeStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        change_status(order, serializer.validated_data["status"])
        return Response(OrderSerializer(order).data)
