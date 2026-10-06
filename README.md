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

## Email yuborish (Gmail)

Email xizmati `users/services/email_service.py` da: `send_email`, `send_verification_code`, `send_reset_code`, `verify_code`.

Gmail orqali yuborish uchun:

1. Gmail akkauntida 2 bosqichli tasdiqlashni yoqing.
2. https://myaccount.google.com/apppasswords sahifasida "App password" yarating.
3. `.env.example` dan `.env` nusxa oling va to'ldiring:

```
EMAIL_HOST_USER=sizning_emailingiz@gmail.com
EMAIL_HOST_PASSWORD=16_xonali_app_password
```

Test paytida xatlarni terminalga chiqarish uchun `.env` ga qo'shing:

```
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

## Swagger

`drf-spectacular` orqali ulangan. Serverni ishga tushiring (`python manage.py runserver`) va oching:

- Swagger UI: http://127.0.0.1:8000/api/docs/
- ReDoc: http://127.0.0.1:8000/api/redoc/
- OpenAPI schema: http://127.0.0.1:8000/api/schema/

Hozircha API endpointlar yozilmagan, shuning uchun hujjat bo'sh ko'rinadi. Viewlar qo'shilgach, avtomatik to'ladi.
