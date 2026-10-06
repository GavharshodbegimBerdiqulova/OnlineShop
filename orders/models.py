from django.conf import settings
from django.db import models

from products.models import Product
from users.models import Address


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Kutilmoqda"
        PAID = "paid", "To'langan"
        SHIPPED = "shipped", "Yo'lda"
        DELIVERED = "delivered", "Yetkazildi"
        CANCELED = "canceled", "Bekor qilindi"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Buyurtma #{self.pk} - {self.user.email}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product} x {self.quantity}"

    @property
    def subtotal(self):
        return self.price * self.quantity
