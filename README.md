# OnlineShop

Django va Django REST Framework asosidagi online do'kon loyihasi: autentifikatsiya (email yoki telefon + tasdiqlash kodi, JWT), mahsulotlar, savat va buyurtmalar. Barcha endpointlar Swagger orqali sinab ko'riladi.

## Texnologiyalar

- Python 3
- Django 6.1
- Django REST Framework
- djangorestframework-simplejwt (JWT token)
- drf-spectacular (Swagger / OpenAPI)
- Pillow (rasmlar uchun)
- python-dotenv (`.env` fayl uchun)
- SQLite (standart baza)

## Loyiha tuzilishi

```
OnlineShop/
├── config/                     Loyiha sozlamalari (settings, urls)
├── users/                      Foydalanuvchi va autentifikatsiya
│   ├── models.py               User, Address, VerificationCode
│   ├── validators.py           Email, telefon, username regexlari
│   ├── permissions.py          IsAdmin, IsAdminOrReadOnly
│   ├── services/
│   │   ├── code_service.py     Kod yuborish/tekshirish, token
│   │   ├── email_service.py    Email yuborish (Gmail)
│   │   ├── sms_service.py      SMS yuborish
│   │   └── token_service.py    JWT yaratish
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── products/                   Kategoriya va mahsulotlar
├── cart/                       Savat
├── orders/                     Buyurtmalar
│   └── services.py             Buyurtma yaratish, bekor qilish, status
├── .env                        Maxfiy sozlamalar (gitga tushmaydi)
├── .env.example                .env uchun namuna
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

Port band bo'lsa, boshqa port bering (bayroqsiz): `python manage.py runserver 8083`. Eski serverni to'xtatish: `lsof -ti :8000 | xargs kill`.

Admin panel: http://127.0.0.1:8000/admin/ (superuser email va paroli bilan). Kategoriya va mahsulotlarni shu yerdan yoki admin tokeni bilan Swaggerdan qo'shish mumkin.

## Modellar

### users

**User** — `AbstractUser` asosidagi custom user. Admin panel va `createsuperuser` email bilan ishlaydi (`USERNAME_FIELD = email`), API'da esa login email, telefon yoki username bilan qilinadi.

| Maydon | Tavsif |
|--------|--------|
| `email` | Unikal, ixtiyoriy (faqat telefon bilan ham ro'yxatdan o'tish mumkin) |
| `phone` | Unikal, ixtiyoriy, `+998XXXXXXXXX` formatida |
| `username` | Unikal, ixtiyoriy |
| `first_name`, `last_name` | Ism va familiya (sign-up da `full_name` dan ajratiladi) |
| `avatar` | Profil rasmi |
| `birth_date` | Tug'ilgan sana |
| `role` | `customer` (mijoz) yoki `admin` |
| `is_verified` | Email yoki telefon tasdiqlangan (sign-up orqali yaratilganlar uchun doim `True`) |

`UserManager` — `create_user` email yoki telefon bilan, `create_superuser` faqat email bilan ishlaydi. Superuser avtomatik `admin` roli va tasdiqlangan holatda yaratiladi.

**Address** — yetkazib berish manzillari (`user`, `title`, `city`, `street`, `zip_code`, `is_default`). Bitta manzil `is_default=True` qilinsa, foydalanuvchining boshqa manzillaridan bu belgi olib tashlanadi.

**VerificationCode** — email yoki telefonga yuboriladigan 4 xonali bir martalik kod: `contact`, `code`, `purpose` (`signup` yoki `reset`), `is_used`, `attempts`, `created_at`. Kod 5 daqiqa amal qiladi, 5 marta noto'g'ri kiritilgach bloklanadi. Kod hali foydalanuvchi yaratilmasdan oldin ham kerak bo'lgani uchun `user` ga emas, `contact` ga bog'langan.

### products

**Category** — `name`, `slug`. **Product** — `category`, `name`, `slug`, `description`, `price`, `stock`, `image`, `is_active`, `created_at`. `slug` bo'sh qoldirilsa, nomdan avtomatik yaratiladi (`iPhone 15` → `iphone-15`, takrorlansa `iphone-15-2`).

### cart

**Cart** — har bir foydalanuvchiga bitta savat. `total_price` — jami narx. **CartItem** — savatdagi mahsulot va uning soni, bitta mahsulot bitta qator (`unique_together`). `subtotal` — narx × soni.

### orders

**Order** — `user`, `address`, `status`, `total_price`, `created_at`. Statuslar: `pending` (kutilmoqda), `paid` (to'langan), `shipped` (yo'lda), `delivered` (yetkazildi), `canceled` (bekor qilindi). **OrderItem** — `product`, `price`, `quantity`. `price` buyurtma vaqtidagi narxni saqlaydi, mahsulot narxi keyin o'zgarsa ham buyurtma o'zgarmaydi.

### Bog'lanishlar

```
User ─┬─< Address
      ├─1 Cart ─< CartItem >─ Product >─ Category
      └─< Order ─< OrderItem >─ Product
              └─ Address
VerificationCode (contact orqali, User ga bog'lanmagan)
```

## Autentifikatsiya

Oqim ilova ekranlariga mos: email yoki telefon → kod → ism va parol → profil rasmi → login.

| # | Qadam | Endpoint |
|---|-------|----------|
| 1 | Email yoki telefon kiritiladi, kod yuboriladi | `POST /api/auth/send-code/` |
| 2 | 4 xonali kod tasdiqlanadi | `POST /api/auth/verify-code/` |
| 3 | Ism va parol kiritilib, user yaratiladi (**Sign Up**) | `POST /api/auth/sign-up/` |
| 4 | Profil rasmi yuklanadi (ixtiyoriy, o'tkazib yuborish mumkin) | `POST /api/auth/me/avatar/` |
| 5 | Email/telefon/username va parol bilan kirish | `POST /api/auth/login/` |

**Ro'yxatdan o'tish**

1. `send-code` ga `{"contact": "+998901234567", "purpose": "signup"}` yuboriladi. Kod email yoki SMS orqali boradi. Kodni qayta yuborish 2 daqiqadan keyin mumkin (oldin so'ralsa `429` va kutish vaqti qaytadi, ekrandagi taymerga mos).
2. `verify-code` ga `{"contact": ..., "purpose": "signup", "code": "1234"}`. To'g'ri bo'lsa `token` qaytadi (15 daqiqa amal qiladi).
3. `sign-up` ga `token`, `full_name`, `password`, `password2` (va ixtiyoriy `username`) yuboriladi. Javobda `access`, `refresh` va `user` qaytadi, ya'ni foydalanuvchi darrov tizimga kiradi.
4. Profil rasmi `multipart/form-data` bilan `avatar` maydonida yuboriladi (5 MB gacha, faqat rasm). Rasmni o'tkazib yuborish uchun hech narsa qilish shart emas. `DELETE` bilan o'chiriladi.

**Login** (`/api/auth/login/`)

```json
{ "login": "ali@gmail.com", "password": "Str0ng!pass9", "remember_me": true }
```

`login` o'rniga telefon (`+998901234567`) yoki username (`ali_01`) ham yozish mumkin. `remember_me=true` bo'lsa refresh token 30 kun, aks holda 1 kun amal qiladi. `access` token 30 daqiqa.

**Parolni unutdim**

1. `send-code` ga `{"contact": ..., "purpose": "reset"}`.
2. `verify-code` ga `purpose: "reset"` bilan kod yuboriladi, `token` olinadi.
3. `reset-password` ga `{"token": ..., "new_password": ...}`.

Foydalanuvchi bazada bor-yo'qligi `reset` da bildirilmaydi, javob doim bir xil.

**Auth endpointlar**

| Metod | Manzil | Token | Tavsif |
|-------|--------|:-----:|--------|
| POST | `/api/auth/send-code/` | yo'q | Kod yuborish (`purpose`: `signup` yoki `reset`) |
| POST | `/api/auth/verify-code/` | yo'q | Kodni tasdiqlash, `token` olish |
| POST | `/api/auth/sign-up/` | yo'q | Foydalanuvchi yaratish |
| POST | `/api/auth/login/` | yo'q | Kirish |
| POST | `/api/auth/token/refresh/` | yo'q | `refresh` orqali yangi `access` olish |
| POST | `/api/auth/logout/` | ha | `refresh` tokenni bekor qilish |
| POST | `/api/auth/reset-password/` | yo'q | Yangi parol o'rnatish |
| POST | `/api/auth/change-password/` | ha | Eski parolni bilib almashtirish |
| GET, PUT, PATCH | `/api/auth/me/` | ha | Profil. `email` va `phone` o'zgarmaydi (tasdiqlangan kontakt) |
| POST, DELETE | `/api/auth/me/avatar/` | ha | Profil rasmini yuklash / o'chirish |
| GET, POST | `/api/addresses/` | ha | O'z manzillari |
| GET, PUT, PATCH, DELETE | `/api/addresses/{id}/` | ha | Manzil bilan ishlash |

**Xavfsizlik**

- Kod 4 xonali bo'lgani uchun 5 ta noto'g'ri urinishdan keyin bloklanadi, 5 daqiqada eskiradi va bir marta ishlatiladi.
- `verify-code` tokeni imzolangan (`django.core.signing`), 15 daqiqa amal qiladi va faqat o'z maqsadi (`signup` yoki `reset`) uchun ishlaydi.
- Parol Django'ning parol tekshiruvlaridan o'tishi kerak.
- Tokensiz so'rovlar daqiqasiga 60 tagacha.
- Logout qilingan refresh token ishlamaydi.

## Email va SMS

Kod email bo'lsa Gmail orqali (`users/services/email_service.py`), telefon bo'lsa SMS orqali (`users/services/sms_service.py`) yuboriladi.

### SMS

Hozircha SMS provayderi ulanmagan: `SMS_BACKEND=console` bo'lganda SMS yuborilmaydi, kod **server terminaliga** chiqadi (`[SMS] +998901234567: ... kodi: 1234`). Rivojlantirish va sinash uchun shu yetarli. Haqiqiy SMS (masalan Eskiz yoki Playmobile) uchun `send_sms()` funksiyasiga provayder chaqiruvini qo'shish va `.env` da `SMS_BACKEND` ni o'zgartirish kerak.

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

### Email xatolari

| Xato | Sabab va yechim |
|------|-----------------|
| `Connection unexpectedly closed` | Google login bosqichida ulanishni uzdi. App Password bekor qilingan yoki akkaunt vaqtincha bloklangan. Eski parolni o'chirib yangisini yarating, https://accounts.google.com/DisplayUnlockCaptcha sahifasida **Continue** bosing, 10–15 daqiqa kuting |
| `Username and Password not accepted` (535) | Parol yoki email noto'g'ri, yoki 2-Step Verification yoqilmagan |
| Xat kelmadi | Spam papkasini tekshiring. `.env` dagi `EMAIL_BACKEND` console bo'lsa, xat faqat terminalga chiqadi |
| `.env` o'zgartirildi, lekin ta'sir qilmadi | Serverni qayta ishga tushiring, `.env` faqat start paytida o'qiladi |

Kod yuborib bo'lmasa (`send-code` 503 qaytaradi), kod bazadan o'chiriladi va qayta urinish mumkin.

## Regex tekshiruvlar

Fayl: `users/validators.py`. Regexlar ikki joyda ishlatiladi:

- **Model maydonlarida** (`User.email`, `User.username`, `User.phone`) `RegexValidator` sifatida.
- **Signup va login serializerlarida**, shuningdek profilni tahrirlashda.

### Email

```
^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$
```

| Qism | Ma'nosi |
|------|---------|
| `[A-Za-z0-9._%+-]+` | `@` dan oldin: harf, raqam va `. _ % + -` belgilari, kamida 1 ta |
| `@` | Bitta `@` belgisi |
| `[A-Za-z0-9-]+` | Domen nomi (`gmail`) |
| `(\.[A-Za-z0-9-]+)*` | Qo'shimcha domen qismlari (`mail.company`), bo'lmasligi ham mumkin |
| `\.[A-Za-z]{2,}` | Oxirgi qism: nuqta va kamida 2 ta harf (`.com`, `.uz`) |

| To'g'ri | Noto'g'ri |
|---------|-----------|
| `ali@gmail.com` | `ali@gmail` (nuqtali domen yo'q) |
| `ali.valiyev+shop@mail.company.uz` | `ali valiyev@gmail.com` (probel bor) |
| `a_b-c@sub-domain.org` | `@gmail.com` (`@` dan oldin hech narsa yo'q) |

Saqlashdan oldin email kichik harfga o'tkaziladi va takrorlanishi katta-kichik harfga bog'liq emas tekshiriladi (`Ali@Gmail.com` va `ali@gmail.com` bir xil).

### Telefon

```
^\+998\d{9}$
```

| Qism | Ma'nosi |
|------|---------|
| `\+998` | O'zbekiston kodi `+998` |
| `\d{9}` | Aynan 9 ta raqam (operator kodi + raqam) |

| To'g'ri | Noto'g'ri |
|---------|-----------|
| `+998901234567` | `+99890123456` (raqam yetishmaydi) |
| | `998901234567` (`+` yo'q, normalizatsiyadan keyin to'g'ri bo'ladi) |
| | `+7901234567` (boshqa davlat) |

Regexdan oldin `normalize_phone()` ishlaydi: probel, `-` va qavslar olib tashlanadi, so'ng:

| Kiritilgan | Natija |
|------------|--------|
| `90 123-45-67` | `+998901234567` |
| `901234567` | `+998901234567` |
| `998901234567` | `+998901234567` |
| `+998 (90) 123-45-67` | `+998901234567` |

Telefon bazada doim shu bir xil formatda saqlanadi va unikal.

### Username

```
^[A-Za-z][A-Za-z0-9_]{2,19}$
```

| Qism | Ma'nosi |
|------|---------|
| `[A-Za-z]` | Birinchi belgi faqat harf |
| `[A-Za-z0-9_]{2,19}` | Keyingi 2-19 belgi: harf, raqam yoki `_` |

Jami uzunlik: 3 dan 20 gacha.

| To'g'ri | Noto'g'ri |
|---------|-----------|
| `ali_01` | `1ali` (raqam bilan boshlanadi) |
| `Shop_User` | `al` (juda qisqa, 3 belgidan kam) |
| `abc` | `ali-01` (`-` mumkin emas) |
| | `ali valiyev` (probel bor) |
| | 21 belgidan uzun nom |

Username takrorlanishi katta-kichik harfga bog'liq emas (`Ali_01` va `ali_01` bir xil).

### Loginda ishlatilishi

`/api/auth/login/` dagi `login` maydoni tartib bilan tekshiriladi (`login_type()`):

1. Email regexiga mos kelsa, email bo'yicha qidiriladi.
2. Aks holda normallashtirilgan qiymat telefon regexiga mos kelsa, telefon bo'yicha qidiriladi.
3. Aks holda username regexiga mos kelsa, username bo'yicha qidiriladi.
4. Hech biriga mos kelmasa, `400` xato qaytadi.

Email `@` belgisi bor, username esa `@` va `+` ni qabul qilmaydi, shuning uchun uchala tur bir-biri bilan chalkashmaydi.

`/api/auth/send-code/` dagi `contact` maydoni faqat email yoki telefon bo'lishi mumkin (username qabul qilinmaydi). `sign-up` dagi `username` esa ixtiyoriy, kiritilsa username regexi bilan tekshiriladi.

## Mahsulotlar

Ko'rish hamma uchun ochiq, qo'shish/o'zgartirish/o'chirish faqat adminlar uchun (`role=admin` yoki `is_staff`). Oddiy foydalanuvchilar faqat `is_active=True` mahsulotlarni ko'radi.

| Metod | Manzil | Kim | Tavsif |
|-------|--------|-----|--------|
| GET | `/api/categories/` | hamma | Kategoriyalar ro'yxati |
| POST | `/api/categories/` | admin | Kategoriya qo'shish |
| GET, PUT, PATCH, DELETE | `/api/categories/{slug}/` | GET hamma, qolganlari admin | Kategoriya bilan ishlash |
| GET | `/api/products/` | hamma | Mahsulotlar ro'yxati (sahifalangan, 12 tadan) |
| POST | `/api/products/` | admin | Mahsulot qo'shish (rasm uchun `multipart/form-data`) |
| GET, PUT, PATCH, DELETE | `/api/products/{slug}/` | GET hamma, qolganlari admin | Mahsulot bilan ishlash |

**Mahsulotlar ro'yxati filtrlari** (`GET /api/products/`)

| Parametr | Tavsif | Misol |
|----------|--------|-------|
| `category` | Kategoriya slug'i | `?category=telefon` |
| `search` | Nom va tavsif bo'yicha qidiruv | `?search=iphone` |
| `min_price`, `max_price` | Narx oralig'i | `?min_price=500&max_price=2000` |
| `in_stock` | Faqat omborda borlari | `?in_stock=true` |
| `ordering` | Saralash: `price`, `-price`, `created_at`, `-created_at`, `name` | `?ordering=-price` |
| `page` | Sahifa raqami | `?page=2` |

## Savat

Barcha endpointlar token talab qiladi, har bir foydalanuvchi faqat o'z savatini ko'radi. Savat birinchi so'rovda avtomatik yaratiladi. Hamma javoblar savatning to'liq holatini qaytaradi (`items`, `total_price`).

| Metod | Manzil | Tavsif |
|-------|--------|--------|
| GET | `/api/cart/` | Savatni ko'rish |
| DELETE | `/api/cart/` | Savatni tozalash |
| POST | `/api/cart/items/` | Mahsulot qo'shish: `{"product": 1, "quantity": 2}`. Mahsulot savatda bo'lsa, soni qo'shiladi |
| PATCH | `/api/cart/items/{id}/` | Sonini o'zgartirish: `{"quantity": 3}` |
| DELETE | `/api/cart/items/{id}/` | Mahsulotni olib tashlash |

Sotuvda bo'lmagan mahsulotni qo'shib bo'lmaydi, soni omborda bor miqdordan oshmasligi kerak.

## Buyurtmalar

| Metod | Manzil | Kim | Tavsif |
|-------|--------|-----|--------|
| POST | `/api/orders/` | foydalanuvchi | Savatdan buyurtma berish: `{"address": 1}` |
| GET | `/api/orders/` | foydalanuvchi (admin hammasini ko'radi) | Buyurtmalar ro'yxati |
| GET | `/api/orders/{id}/` | egasi yoki admin | Buyurtma tafsiloti |
| POST | `/api/orders/{id}/cancel/` | egasi | Bekor qilish (faqat `pending`) |
| PATCH | `/api/orders/{id}/status/` | admin | Holatni o'zgartirish: `{"status": "paid"}` |

**Buyurtma berilganda:**

1. Savat bo'sh bo'lmasligi, manzil foydalanuvchiga tegishli bo'lishi kerak.
2. Har bir mahsulot sotuvda va omborda yetarli ekani tekshiriladi.
3. Buyurtma va uning qatorlari yaratiladi, narx shu paytdagi narxda saqlanadi.
4. Ombordagi son kamaytiriladi, savat tozalanadi. Hammasi bitta tranzaksiyada bajariladi, xato bo'lsa hech narsa o'zgarmaydi.

**Bekor qilinganda** mahsulotlar omborga qaytariladi.

**Status o'zgarishi** faqat quyidagi yo'nalishlarda mumkin:

```
pending ─> paid ─> shipped ─> delivered
   └─────────┴─> canceled
```

To'lov tizimi ulanmagan, `paid` holatini admin qo'lda belgilaydi.

## So'rov va javob namunalari

Xatolar `400` (noto'g'ri ma'lumot), `401` (token yo'q yoki eskirgan), `403` (ruxsat yo'q), `404` (topilmadi), `429` (juda tez-tez), `503` (kod yuborib bo'lmadi) kodlari bilan qaytadi. Validatsiya xatosi maydon nomi bilan keladi: `{"password2": ["Parollar bir xil emas"]}`, umumiy xato esa `{"detail": "..."}` ko'rinishida.

### Auth

**`POST /api/auth/send-code/`**

```json
{ "contact": "+998901234567", "purpose": "signup" }
```
```json
{ "detail": "Tasdiqlash kodi yuborildi", "resend_after": 120 }
```

`purpose`: `signup` yoki `reset`. `contact`: email yoki telefon.

**`POST /api/auth/verify-code/`**

```json
{ "contact": "+998901234567", "purpose": "signup", "code": "1234" }
```
```json
{ "token": "eyJjb250YWN0Ijoi..." }
```

**`POST /api/auth/sign-up/`**

```json
{
  "token": "eyJjb250YWN0Ijoi...",
  "full_name": "Ali Valiyev",
  "username": "ali_01",
  "password": "Str0ng!pass9",
  "password2": "Str0ng!pass9"
}
```
```json
{
  "access": "eyJ...",
  "refresh": "eyJ...",
  "user": {
    "id": 1, "full_name": "Ali Valiyev", "first_name": "Ali", "last_name": "Valiyev",
    "username": "ali_01", "email": null, "phone": "+998901234567",
    "avatar": null, "birth_date": null, "role": "customer"
  }
}
```

`username` ixtiyoriy.

**`POST /api/auth/login/`**

```json
{ "login": "ali_01", "password": "Str0ng!pass9", "remember_me": true }
```

Javob `sign-up` javobi bilan bir xil: `access`, `refresh`, `user` (status `200`). Login yoki parol xato bo'lsa `{"detail": "Login yoki parol noto'g'ri"}`.

**`POST /api/auth/token/refresh/`**

```json
{ "refresh": "eyJ..." }
```
```json
{ "access": "eyJ...", "refresh": "eyJ..." }
```

Har safar yangi `refresh` beriladi, eskisi bekor bo'ladi. Keyingi so'rovda yangisini ishlating.

**`POST /api/auth/logout/`** (token kerak)

```json
{ "refresh": "eyJ..." }
```

**`POST /api/auth/reset-password/`**

```json
{ "token": "eyJjb250YWN0Ijoi...", "new_password": "N3w!password" }
```

**`POST /api/auth/change-password/`** (token kerak)

```json
{ "old_password": "Str0ng!pass9", "new_password": "N3w!password" }
```

**`GET /api/auth/me/`, `PATCH /api/auth/me/`** (token kerak)

```json
{ "first_name": "Sher", "last_name": "Aliyev", "username": "sher_01", "birth_date": "2000-05-20" }
```

O'zgartirish mumkin: `first_name`, `last_name`, `username`, `birth_date`, `avatar`. O'zgarmaydi: `email`, `phone`, `role`.

**`POST /api/auth/me/avatar/`** (token kerak, `multipart/form-data`)

```
avatar: <rasm fayli, 5 MB gacha>
```

Javob: yangilangan profil (`avatar` maydonida rasm manzili). `DELETE` bilan rasm o'chiriladi (`204`).

### Manzillar (token kerak)

**`POST /api/addresses/`**

```json
{ "title": "Uy", "city": "Toshkent", "street": "Amir Temur 1", "zip_code": "100000", "is_default": true }
```
```json
{ "id": 1, "title": "Uy", "city": "Toshkent", "street": "Amir Temur 1", "zip_code": "100000", "is_default": true }
```

### Kategoriya va mahsulot (yozish uchun admin tokeni kerak)

**`POST /api/categories/`**

```json
{ "name": "Telefon" }
```
```json
{ "id": 1, "name": "Telefon", "slug": "telefon" }
```

**`POST /api/products/`** (rasm bilan yuborish uchun `multipart/form-data`)

```json
{ "category": 1, "name": "iPhone 15", "description": "128 GB", "price": "1000.00", "stock": 5, "is_active": true }
```
```json
{
  "id": 1, "category": 1, "category_name": "Telefon", "name": "iPhone 15", "slug": "iphone-15",
  "description": "128 GB", "price": "1000.00", "stock": 5, "image": null,
  "is_active": true, "created_at": "2026-10-06T12:00:00Z"
}
```

**`GET /api/products/?category=telefon&ordering=-price&page=1`**

```json
{ "count": 1, "next": null, "previous": null, "results": [ { "id": 1, "name": "iPhone 15", "slug": "iphone-15", "price": "1000.00" } ] }
```

(`results` ichida har bir mahsulot yuqoridagi to'liq ko'rinishda keladi.)

### Savat (token kerak)

**`POST /api/cart/items/`**

```json
{ "product": 1, "quantity": 2 }
```

**`PATCH /api/cart/items/{id}/`**

```json
{ "quantity": 3 }
```

Savat bilan ishlaydigan hamma endpoint (`GET`, `DELETE /api/cart/`, `POST /api/cart/items/`, `PATCH` va `DELETE /api/cart/items/{id}/`) savatning to'liq holatini qaytaradi:

```json
{
  "id": 1,
  "items": [
    {
      "id": 1,
      "product": { "id": 1, "name": "iPhone 15", "slug": "iphone-15", "price": "1000.00", "image": null, "stock": 5 },
      "quantity": 2,
      "subtotal": "2000.00"
    }
  ],
  "total_price": "2000.00"
}
```

### Buyurtma (token kerak)

**`POST /api/orders/`**

```json
{ "address": 1 }
```
```json
{
  "id": 1, "user": 1, "status": "pending", "status_display": "Kutilmoqda",
  "address": 1, "address_text": "Uy: Toshkent, Amir Temur 1",
  "total_price": "2000.00",
  "items": [ { "id": 1, "product": 1, "product_name": "iPhone 15", "price": "1000.00", "quantity": 2, "subtotal": "2000.00" } ],
  "created_at": "2026-10-06T12:30:00Z"
}
```

`GET /api/orders/`, `GET /api/orders/{id}/`, `POST /api/orders/{id}/cancel/` (so'rov tanasi yo'q) va `PATCH /api/orders/{id}/status/` shu ko'rinishdagi buyurtmani qaytaradi.

**`PATCH /api/orders/{id}/status/`** (faqat admin)

```json
{ "status": "paid" }
```

`status`: `pending`, `paid`, `shipped`, `delivered`, `canceled`.

### Sinov endpointi

**`POST /api/send-test-email/`** (token shart emas)

```json
{ "email": "manzil@gmail.com", "subject": "OnlineShop test", "message": "Salom" }
```
```json
{ "detail": "Xat yuborildi" }
```

## Swagger

`drf-spectacular` orqali ulangan. Server ishlaganda:

| Manzil | Tavsif |
|--------|--------|
| http://127.0.0.1:8000/api/docs/ | Swagger UI |
| http://127.0.0.1:8000/api/redoc/ | ReDoc |
| http://127.0.0.1:8000/api/schema/ | OpenAPI schema |

Endpointlar `auth`, `profile`, `addresses`, `categories`, `products`, `cart`, `orders`, `email` guruhlarida chiqadi.

**Swaggerda to'liq sinash tartibi**

1. `auth` bo'limida `send-code` → `verify-code` → `sign-up`. Telefon bilan sinasangiz, kodni server terminalidan oling.
2. Javobdagi `access` tokenni yuqoridagi **Authorize** tugmasiga kiriting (faqat tokenning o'zini, `Bearer` so'zisiz).
3. Admin sifatida kategoriya va mahsulot qo'shish uchun `createsuperuser` bilan yaratilgan emailingiz va parolingiz bilan `login` qiling, olingan `access` ni Authorize ga kiriting.
4. Oddiy foydalanuvchi bilan: `cart/items` ga mahsulot qo'shing → `addresses` ga manzil qo'shing → `orders` ga buyurtma bering.

### Email yuborishni sinash

`POST /api/send-test-email/` ga email yozilsa, shu manzilga sinov xati boradi:

```json
{
  "email": "manzil@gmail.com",
  "subject": "OnlineShop test",
  "message": "Gmail orqali yuborish ishlayapti."
}
```

Bu endpoint faqat sinov uchun, autentifikatsiyasiz ochiq. Loyiha tayyor bo'lgach o'chirib tashlang.

## Eslatmalar

- Ro'yxat endpointlari (`products`, `orders`, `addresses`) sahifalangan: javob `count`, `next`, `previous`, `results` shaklida.
- Rasmlar `media/` papkasida saqlanadi va `DEBUG=True` bo'lganda `/media/...` orqali beriladi.
- Testlar yozilmagan.
