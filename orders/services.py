from django.db import transaction
from rest_framework.exceptions import ValidationError

from cart.models import Cart
from products.models import Product

from .models import Order, OrderItem

ALLOWED_STATUSES = {
    Order.Status.PENDING: [Order.Status.PAID, Order.Status.CANCELED],
    Order.Status.PAID: [Order.Status.SHIPPED, Order.Status.CANCELED],
    Order.Status.SHIPPED: [Order.Status.DELIVERED],
    Order.Status.DELIVERED: [],
    Order.Status.CANCELED: [],
}


@transaction.atomic
def create_order(user, address):
    cart = Cart.objects.filter(user=user).first()
    items = list(cart.items.select_related("product")) if cart else []
    if not items:
        raise ValidationError({"detail": "Savat bo'sh"})

    products = {
        product.id: product
        for product in Product.objects.select_for_update().filter(id__in=[item.product_id for item in items])
    }

    order = Order.objects.create(user=user, address=address)
    total = 0
    for item in items:
        product = products[item.product_id]
        if not product.is_active:
            raise ValidationError({"detail": f"{product.name} sotuvda yo'q"})
        if item.quantity > product.stock:
            raise ValidationError({"detail": f"{product.name} uchun omborda faqat {product.stock} ta mavjud"})
        OrderItem.objects.create(order=order, product=product, price=product.price, quantity=item.quantity)
        product.stock -= item.quantity
        product.save(update_fields=["stock"])
        total += product.price * item.quantity

    order.total_price = total
    order.save(update_fields=["total_price"])
    cart.items.all().delete()
    return order


@transaction.atomic
def change_status(order, new_status):
    if new_status not in ALLOWED_STATUSES[order.status]:
        raise ValidationError({"status": f"{order.get_status_display()} holatidan {new_status} ga o'tib bo'lmaydi"})

    if new_status == Order.Status.CANCELED:
        for item in order.items.select_related("product"):
            if item.product:
                item.product.stock += item.quantity
                item.product.save(update_fields=["stock"])

    order.status = new_status
    order.save(update_fields=["status"])
    return order
