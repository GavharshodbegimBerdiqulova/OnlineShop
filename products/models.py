from django.db import models


class Category(models.Model):
    name = models.CharField("Nomi", max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    name = models.CharField("Nomi", max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField("Tavsif", blank=True)
    price = models.DecimalField("Narxi", max_digits=12, decimal_places=2)
    stock = models.PositiveIntegerField("Omborda", default=0)
    image = models.ImageField("Rasm", upload_to="products/", blank=True, null=True)
    is_active = models.BooleanField("Sotuvda", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Mahsulot"
        verbose_name_plural = "Mahsulotlar"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
