# Wolf Host

[![Wolf Host CI](https://github.com/3MH-Technologies/wolf-host/actions/workflows/ci.yml/badge.svg)](https://github.com/3MH-Technologies/wolf-host/actions/workflows/ci.yml)
[![License: All Rights Reserved](https://img.shields.io/badge/license-All%20Rights%20Reserved-red)](LICENSE)

منصة استضافة احترافية لبوتات بايثون — مشابهة في تجربتها لـ Railway وCoolify وPterodactyl، مبنية بالكامل بمعايير Production.

**3MH Technologies** | https://3mh.pages.dev/ar/

## المزايا

- تشغيل كل بوت داخل Docker Container معزول تمامًا (لا صلاحيات مرتفعة، لا وصول لـ Host، حدود CPU/RAM/Disk/Processes)
- رفع الكود عبر ZIP أو ملف واحد (الرفع من Git Repository قريباً)
- اكتشاف وتثبيت المكتبات تلقائيًا (requirements.txt أو تحليل imports)
- سجلات مباشرة (Live Logs) عبر Server-Sent Events
- مدير ملفات كامل (رفع، تعديل، حذف، نقل، نسخ)
- طرفية محدودة الصلاحيات لكل بوت
- إعادة تشغيل تلقائي عند التعطل (مراقبة دورية عبر Celery)
- نظام خطط واشتراكات (Free / Basic / Pro / Enterprise)
- مدفوعات عبر Stripe (تأكيد عبر Webhook) وUSDT (TRC20 / BEP20) مع تحقق فعلي من المعاملات — PayPal قيد التطوير
- كوبونات خصم
- لوحة إدارة كاملة: إحصائيات، إدارة مستخدمين، إيقاف/حذف قسري للبوتات
- مصادقة ثنائية (2FA / TOTP)، إدارة الجلسات والأجهزة (إنشاء مفاتيح API متوفر، والمصادقة بها قريباً)
- سجل تدقيق كامل (Audit Log) لكل الإجراءات الحساسة
- واجهة عربية/إنجليزية مع دعم RTL كامل، وضع داكن

## البنية التقنية

| الطبقة | التقنية |
|---|---|
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.13, SQLAlchemy 2, Alembic |
| Database | PostgreSQL 17 |
| Cache/Queue | Redis 7, Celery |
| Orchestration | Docker, Docker Compose |
| Reverse Proxy | Nginx |

## البدء السريع

```bash
git clone https://github.com/3MH-Technologies/wolf-host.git wolfhost
cd wolfhost
cp .env.example .env
# عدّل .env وضع القيم الحقيقية (كلمات مرور، مفاتيح API، إلخ)
./scripts/deploy.sh
```

- إن لم توجد شهادة SSL في `nginx/certs/`، ينشئ `deploy.sh` شهادة ذاتية التوقيع تلقائيًا (صالحة للاختبار — استبدلها بشهادة حقيقية، مثل Let's Encrypt، في الإنتاج).
- المنصة ستكون متاحة على `https://yourdomain.com` بعد ضبط `NEXT_PUBLIC_API_URL` و`CORS_ORIGINS` في `.env`.

## التطوير المحلي

```bash
cp .env.example .env
docker compose -f docker-compose.dev.yml up
```

Backend: http://localhost:8000/api/docs
Frontend: http://localhost:3000

## هيكل المشروع

```
wolfhost/
├── backend/          FastAPI application
├── frontend/         Next.js application
├── docker/           Dockerfiles
├── nginx/            Reverse proxy config
├── scripts/          Deploy, backup, restore, healthcheck
├── docs/             Architecture, API, deployment docs
└── docker-compose.yml
```

مزيد من التفاصيل: [الهيكلة المعمارية](docs/ARCHITECTURE.md) · [توثيق الـ API](docs/API.md) · [دليل النشر](docs/DEPLOYMENT.md) · [توثيق Docker](docs/DOCKER.md) · [مخطط قاعدة البيانات](docs/ER_DIAGRAM.md) · [سياسة الأمان](.github/SECURITY.md)

## الترخيص

جميع الحقوق محفوظة — راجع [LICENSE](LICENSE).

© 3MH Technologies — https://3mh.pages.dev/ — https://t.me/j49_c
