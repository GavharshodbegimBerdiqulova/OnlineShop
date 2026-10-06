# OnlineShop

Django va Django REST Framework asosidagi online do'kon loyihasi.

Hozirgi holat: modellar, email yuborish xizmati va Swagger hujjati tayyor. Auth, savat va buyurtma API'lari keyingi bosqichda yoziladi.

## Texnologiyalar

- Python 3
- Django 6.1
- Django REST Framework
- drf-spectacular (Swagger / OpenAPI)
- Pillow (rasmlar uchun)
- python-dotenv (`.env` fayl uchun)
- SQLite (standart baza)

## Loyiha tuzilishi

```
OnlineShop/
├── config/                  Loyiha sozlamalari (settings, urls)
├── users/                   Foydalanuvchi va autentifikatsiya
│   ├── models.py            User, Address, VerificationCode
│   ├── services/
│   │   └── email_service.py Email yuborish xizmati
│   ├── serializers.py       Test email serializeri
│   ├── views.py             Test email endpointi
│   └── urls.py
├── products/                Kategoriya va mahsulotlar
├── cart/                    Savat
├── orders/                  Buyurtmalar
├── .env                     Maxfiy sozlamalar (gitga tushmaydi)
├── .env.example             .env uchun namuna
└── requirements.txt
```

## O'rnatish va ishga tushirish

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Yangi terminal ochilganda `source venv/bin/activate` ni qayta bajarish kerak.

Port band bo'lsa, boshqa port bering (bayroqsiz):

```bash
python manage.py runserver 8083
```

Eski serverni to'xtatish: `lsof -ti :8000 | xargs kill`

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

### Bog'lanishlar

```
User ─┬─< Address
      ├─< VerificationCode
      ├─1 Cart ─< CartItem >─ Product >─ Category
      └─< Order ─< OrderItem >─ Product
              └─ Address
```

## Email xizmati

Fayl: `users/services/email_service.py`

| Funksiya | Vazifasi |
|----------|----------|
| `send_email(to_email, subject, message)` | Oddiy xat yuboradi |
| `send_verification_code(user)` | Email tasdiqlash kodini yaratadi va yuboradi |
| `send_reset_code(user)` | Parolni tiklash kodini yaratadi va yuboradi |
| `verify_code(user, code, purpose)` | Kodni tekshiradi. To'g'ri, ishlatilmagan va 5 daqiqadan oshmagan bo'lsa `True` qaytaradi va kodni ishlatilgan deb belgilaydi |

Yangi kod so'ralganda, shu maqsad uchun eski ishlatilmagan kodlar bekor qilinadi.

Misol:

```python
from users.services.email_service import send_verification_code, verify_code

send_verification_code(user)
verify_code(user, "123456", "email")
```

### Gmail sozlash

Gmail orqali yuborish uchun oddiy parol emas, **App Password** kerak.

1. https://myaccount.google.com/security sahifasida **2-Step Verification** ni yoqing.
2. https://myaccount.google.com/apppasswords sahifasida App Password yarating (16 belgi).
3. `.env` faylini to'ldiring (parolni probelsiz yozing):

```
EMAIL_HOST_USER=sizning_emailingiz@gmail.com
EMAIL_HOST_PASSWORD=16belgiliapppassword
```

Xatlarni yuborish o'rniga terminalga chiqarish uchun (test paytida) `.env` ga qo'shing:

```
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

`.env` faylini hech qachon gitga yuklamang va parolni boshqalarga yubormang. Parol oshkor bo'lsa, apppasswords sahifasidan o'chirib, yangisini yarating.

### Xatolar

| Xato | Sabab va yechim |
|------|-----------------|
| `Connection unexpectedly closed` | Google login bosqichida ulanishni uzdi. App Password bekor qilingan yoki akkaunt vaqtincha bloklangan. Eski parolni o'chirib yangisini yarating, https://accounts.google.com/DisplayUnlockCaptcha sahifasida **Continue** bosing, 10–15 daqiqa kuting |
| `Username and Password not accepted` (535) | Parol yoki email noto'g'ri, yoki 2-Step Verification yoqilmagan |
| Xat kelmadi | Spam papkasini tekshiring. `.env` dagi `EMAIL_BACKEND` console bo'lsa, xat faqat terminalga chiqadi |
| `.env` o'zgartirildi, lekin ta'sir qilmadi | Serverni qayta ishga tushiring, `.env` faqat start paytida o'qiladi |

## Swagger

`drf-spectacular` orqali ulangan. Server ishlaganda:

| Manzil | Tavsif |
|--------|--------|
| http://127.0.0.1:8000/api/docs/ | Swagger UI |
| http://127.0.0.1:8000/api/redoc/ | ReDoc |
| http://127.0.0.1:8000/api/schema/ | OpenAPI schema |

### API endpointlar

| Metod | Manzil | Tavsif |
|-------|--------|--------|
| POST | `/api/send-test-email/` | Email yuborishni sinash uchun |

**Email yuborishni Swaggerdan sinash**

1. `python manage.py runserver` bilan serverni ishga tushiring.
2. `/api/docs/` sahifasini oching.
3. `email` bo'limida **POST /api/send-test-email/** ni oching va **Try it out** bosing.
4. Quyidagicha to'ldiring va **Execute** bosing:

```json
{
  "email": "manzil@gmail.com",
  "subject": "OnlineShop test",
  "message": "Gmail orqali yuborish ishlayapti."
}
```

Muvaffaqiyatli javob: `{"detail": "Xat yuborildi"}`. Xato bo'lsa, `detail` ichida xato matni chiqadi.

Bu endpoint faqat sinov uchun, autentifikatsiyasiz ochiq. Loyiha tayyor bo'lgach o'chirib tashlang.

## Keyingi qadamlar

- Auth API: register, emailni tasdiqlash, login (JWT), parolni tiklash, profil
- Mahsulotlar va kategoriyalar API'si
- Savat va buyurtma API'si
- Admin panel sozlamalari
