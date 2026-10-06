from decimal import Decimal, InvalidOperation

from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import filters, viewsets
from rest_framework.exceptions import ValidationError

from users.permissions import IsAdminOrReadOnly, is_admin

from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer


def parse_price(value, name):
    try:
        return Decimal(value)
    except InvalidOperation:
        raise ValidationError({name: "Son kiriting"})


@extend_schema(tags=["categories"])
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by("name")
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "slug"
    pagination_class = None


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter("category", str, description="Kategoriya slug'i"),
            OpenApiParameter("min_price", str, description="Eng kam narx"),
            OpenApiParameter("max_price", str, description="Eng yuqori narx"),
            OpenApiParameter("in_stock", bool, description="Faqat omborda borlari"),
        ]
    )
)
@extend_schema(tags=["products"])
class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "slug"
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["price", "created_at", "name"]

    def get_queryset(self):
        queryset = Product.objects.select_related("category")
        if not is_admin(self.request.user):
            queryset = queryset.filter(is_active=True)

        params = self.request.query_params
        if params.get("category"):
            queryset = queryset.filter(category__slug=params["category"])
        if params.get("min_price"):
            queryset = queryset.filter(price__gte=parse_price(params["min_price"], "min_price"))
        if params.get("max_price"):
            queryset = queryset.filter(price__lte=parse_price(params["max_price"], "max_price"))
        if params.get("in_stock", "").lower() in ("true", "1"):
            queryset = queryset.filter(stock__gt=0)
        return queryset
