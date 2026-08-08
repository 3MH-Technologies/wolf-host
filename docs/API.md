# Wolf Host — API Documentation

التوثيق التفاعلي الكامل (OpenAPI/Swagger) متاح تلقائيًا على:

- Swagger UI: `/api/docs`
- ReDoc: `/api/redoc`
- OpenAPI JSON: `/api/openapi.json`

جميع المسارات تحت البادئة `/api/v1`.

## المصادقة (`/auth`)

| Method | Path | الوصف |
|---|---|---|
| POST | `/auth/register` | تسجيل مستخدم جديد |
| POST | `/auth/login` | تسجيل الدخول (يدعم 2FA) |
| POST | `/auth/refresh` | تجديد access token |
| POST | `/auth/logout` | إبطال الجلسة الحالية |
| POST | `/auth/forgot-password` | طلب إعادة تعيين كلمة المرور |
| POST | `/auth/reset-password` | تنفيذ إعادة التعيين |
| POST | `/auth/2fa/enable` | توليد سر TOTP |
| POST | `/auth/2fa/verify` | تفعيل 2FA بعد التحقق |
| POST | `/auth/2fa/disable` | تعطيل 2FA |

جميع المسارات المحمية تتطلب `Authorization: Bearer <access_token>`.

## المستخدم (`/users`)

| Method | Path | الوصف |
|---|---|---|
| GET | `/users/me` | الملف الشخصي |
| PUT | `/users/me/password` | تغيير كلمة المرور |
| GET | `/users/me/sessions` | الجلسات النشطة |
| DELETE | `/users/me/sessions/{id}` | إنهاء جلسة |
| POST | `/users/me/api-keys` | إنشاء مفتاح API |
| GET | `/users/me/api-keys` | قائمة المفاتيح |
| DELETE | `/users/me/api-keys/{id}` | إبطال مفتاح |
| GET | `/users/me/notifications` | الإشعارات |

## البوتات (`/bots`)

| Method | Path | الوصف |
|---|---|---|
| POST | `/bots` | إنشاء بوت جديد |
| GET | `/bots` | قائمة بوتات المستخدم |
| GET | `/bots/{id}` | تفاصيل بوت |
| POST | `/bots/{id}/upload` | رفع ملف أو ZIP |
| POST | `/bots/{id}/start` | تشغيل |
| POST | `/bots/{id}/stop` | إيقاف |
| POST | `/bots/{id}/restart` | إعادة تشغيل |
| DELETE | `/bots/{id}` | حذف نهائي |
| PUT | `/bots/{id}/env` | تحديث متغيرات البيئة |
| GET | `/bots/{id}/logs` | السجلات (نصية) |
| GET | `/bots/{id}/logs/stream` | السجلات المباشرة (SSE) |
| GET | `/bots/{id}/stats` | استهلاك CPU/RAM/الشبكة |
| GET/PUT/DELETE | `/bots/{id}/files*` | مدير الملفات الكامل |
| POST | `/bots/{id}/console` | تنفيذ أمر محدود الصلاحيات |

## الفوترة (`/billing`)

| Method | Path | الوصف |
|---|---|---|
| GET | `/billing/plans` | الخطط المتاحة |
| POST | `/billing/invoices` | إنشاء فاتورة (Stripe/PayPal/USDT) |
| GET | `/billing/invoices` | فواتير المستخدم |
| POST | `/billing/invoices/{id}/confirm-crypto` | تأكيد دفع USDT بهاش المعاملة |
| POST | `/billing/webhooks/stripe` | Webhook استقبال أحداث Stripe |

## الإدارة (`/admin`) — تتطلب دور admin أو super_admin

| Method | Path | الوصف |
|---|---|---|
| GET | `/admin/stats` | إحصائيات المنصة |
| GET | `/admin/users` | كل المستخدمين |
| POST | `/admin/users/{id}/suspend` | إيقاف مستخدم |
| POST | `/admin/users/{id}/unsuspend` | إلغاء الإيقاف |
| GET | `/admin/bots` | كل البوتات |
| POST | `/admin/bots/{id}/force-stop` | إيقاف قسري |
| DELETE | `/admin/bots/{id}/force-delete` | حذف قسري |
| POST | `/admin/coupons` | إنشاء كوبون خصم |
| GET | `/admin/docker/containers` | حاويات Docker المُدارة |
