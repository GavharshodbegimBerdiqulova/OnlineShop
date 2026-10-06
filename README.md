# OnlineShop

Django va Django REST Framework asosidagi online do'kon loyihasi.

Hozirgi holat: modellar, email xizmati, Swagger hujjati va to'liq auth API (JWT) tayyor. Mahsulot, savat va buyurtma API'lari keyingi bosqichda yoziladi.

## Texnologiyalar

- Python 3
- Django 6.1
- Django REST Framework
- drf-spectacular (Swagger / OpenAPI)
- djangorestframework-simplejwt (JWT token)
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
│   ├── serializers.py       Auth, profil va manzil serializerlari
│   ├── views.py             Auth, profil, manzil va test email viewlari
│   └── urls.py              /api/ manzillari
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

### Auth API

Hamma auth endpointlar `/api/auth/` ostida. Himoyalangan endpointlarga `Authorization: Bearer <access_token>` header kerak. Swaggerda yuqoridagi **Authorize** tugmasiga faqat `access` tokenni kiriting.

| Metod | Manzil | Token | Tavsif |
|-------|--------|:-----:|--------|
| POST | `/api/auth/register/` | yo'q | Ro'yxatdan o'tish, emailga 6 xonali kod yuboriladi |
| POST | `/api/auth/verify-email/` | yo'q | Email va kod bilan emailni tasdiqlash |
| POST | `/api/auth/resend-code/` | yo'q | Tasdiqlash kodini qayta yuborish |
| POST | `/api/auth/login/` | yo'q | Email va parol bilan kirish, `access` va `refresh` token qaytaradi |
| POST | `/api/auth/token/refresh/` | yo'q | `refresh` orqali yangi `access` olish |
| POST | `/api/auth/logout/` | ha | `refresh` tokenni bekor qilish |
| POST | `/api/auth/forgot-password/` | yo'q | Parolni tiklash kodini emailga yuborish |
| POST | `/api/auth/reset-password/` | yo'q | Kod bilan yangi parol o'rnatish |
| POST | `/api/auth/change-password/` | ha | Eski parolni bilib, yangisiga almashtirish |
| GET, PUT, PATCH | `/api/auth/me/` | ha | Profilni ko'rish va tahrirlash |
| GET, POST | `/api/addresses/` | ha | O'z manzillari ro'yxati va yangi manzil qo'shish |
| GET, PUT, PATCH, DELETE | `/api/addresses/{id}/` | ha | Manzilni ko'rish, o'zgartirish, o'chirish |
| POST | `/api/send-test-email/` | yo'q | Email yuborishni sinash (faqat sinov uchun) |

**Auth oqimi**

1. `register` — foydalanuvchi yaratiladi (`is_verified=False`), emailga kod boradi.
2. `verify-email` — kod to'g'ri bo'lsa, email tasdiqlanadi. Tasdiqlanmagan foydalanuvchi login qila olmaydi.
3. `login` — `access` (30 daqiqa) va `refresh` (7 kun) token olinadi.
4. Token tugasa, `token/refresh` bilan yangilanadi. `logout` refresh tokenni bekor qiladi.
5. Parol esdan chiqsa: `forgot-password` → emailga kod → `reset-password`.

**Qoidalar**

- Parol Django'ning parol tekshiruvlaridan o'tishi kerak (kamida 8 belgi, juda oddiy bo'lmasligi, faqat raqamlardan iborat bo'lmasligi).
- Kod 5 daqiqa amal qiladi va faqat bir marta ishlatiladi.
- `forgot-password` va `resend-code` email bazada bor-yo'qligini bildirmaydi, har doim bir xil javob qaytaradi.
- Tokensiz so'rovlar soni cheklangan (daqiqasiga 60 ta).
- `createsuperuser` bilan yaratilgan admin avtomatik tasdiqlangan bo'ladi.

**Namuna so'rovlar**

```json
POST /api/auth/register/
{
  "email": "ali@gmail.com",
  "first_name": "Ali",
  "last_name": "Valiyev",
  "phone": "+998901234567",
  "password": "Str0ng!pass9",
  "password2": "Str0ng!pass9"
}
```

```json
POST /api/auth/verify-email/
{ "email": "ali@gmail.com", "code": "123456" }
```

```json
POST /api/auth/login/
{ "email": "ali@gmail.com", "password": "Str0ng!pass9" }
```

```json
POST /api/auth/reset-password/
{ "email": "ali@gmail.com", "code": "123456", "new_password": "N3w!password" }
```

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

- Mahsulotlar va kategoriyalar API'si
- Savat va buyurtma API'si
- Admin panel sozlamalari
