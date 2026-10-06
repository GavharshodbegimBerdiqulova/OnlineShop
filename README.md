# OnlineShop

Django asosidagi online do'kon loyihasi. Hozircha faqat model qismi yozilgan.

## O'rnatish

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Applar

| App | Vazifasi |
|-----|----------|
| `users` | Foydalanuvchi va autentifikatsiya (to'liq) |
| `products` | Kategoriya va mahsulotlar |
| `cart` | Savat |
| `orders` | Buyurtmalar |

## Modellar

### users

**User** — `AbstractUser` asosidagi custom user. Login `email` orqali bo'ladi, `username` ishlatilmaydi.

| Maydon | Tavsif |
|--------|--------|
| `email` | Unikal, login uchun ishlatiladi |
| `phone` | Telefon raqami |
| `avatar` | Profil rasmi |
| `birth_date` | Tug'ilgan sana |
| `role` | `customer` (mijoz) yoki `admin` |
| `is_verified` | Email tasdiqlanganmi |

`UserManager` — `create_user` va `create_superuser` metodlari email bilan ishlaydi. Superuser avtomatik `admin` roli va tasdiqlangan holatda yaratiladi.

**Address** — foydalanuvchining yetkazib berish manzillari (`user`, `title`, `city`, `street`, `zip_code`, `is_default`). Bitta manzil `is_default=True` qilinsa, foydalanuvchining boshqa manzillaridan bu belgi olib tashlanadi.

**VerificationCode** — email tasdiqlash (`email`) va parolni tiklash (`reset`) uchun 6 xonali bir martalik kod. Kod yaratilgandan keyin 5 daqiqa amal qiladi (`is_expired()`), ishlatilgach `is_used=True` bo'ladi.

### products

**Category** — kategoriya (`name`, `slug`).

**Product** — mahsulot: `category`, `name`, `slug`, `description`, `price`, `stock` (ombordagi soni), `image`, `is_active` (sotuvdami), `created_at`.

### cart

**Cart** — har bir foydalanuvchiga bitta savat (`OneToOne`). `total_price` — savatdagi barcha mahsulotlar jami narxi.

**CartItem** — savatdagi mahsulot va uning soni (`quantity`). Bitta mahsulot savatda faqat bitta qator bo'lib turadi (`unique_together`). `subtotal` — narx × soni.

### orders

**Order** — buyurtma: `user`, `address`, `status`, `total_price`, `created_at`.

Statuslar: `pending` (kutilmoqda), `paid` (to'langan), `shipped` (yo'lda), `delivered` (yetkazildi), `canceled` (bekor qilindi).

**OrderItem** — buyurtmadagi mahsulot: `product`, `price`, `quantity`. `price` buyurtma vaqtidagi narxni saqlaydi, shuning uchun mahsulot narxi keyin o'zgarsa ham buyurtma o'zgarmaydi.

## Bog'lanishlar

```
User ─┬─< Address
      ├─< VerificationCode
      ├─1 Cart ─< CartItem >─ Product >─ Category
      └─< Order ─< OrderItem >─ Product
              └─ Address
```
