# Wolf Host

منصة استضافة احترافية لبوتات بايثون — مشابهة في تجربتها لـ Railway وCoolify وPterodactyl، مبنية بالكامل بمعايير Production.

**3MH Technologies** | https://3mh.pages.dev/ar/

## المزايا

- تشغيل كل بوت داخل Docker Container معزول تمامًا (لا صلاحيات مرتفعة، لا وصول لـ Host، حدود CPU/RAM/Disk/Processes)
- رفع الكود عبر ZIP، ملف واحد، أو Git Repository
- اكتشاف وتثبيت المكتبات تلقائيًا (requirements.txt أو تحليل imports)
- سجلات مباشرة (Live Logs) عبر Server-Sent Events
- مدير ملفات كامل (رفع، تعديل، حذف، نقل، نسخ)
- طرفية محدودة الصلاحيات لكل بوت
- إعادة تشغيل تلقائي عند التعطل (مراقبة دورية عبر Celery)
- نظام خطط واشتراكات (Free / Basic / Pro / Enterprise)
- مدفوعات عبر Stripe وPayPal وUSDT (TRC20 / BEP20) مع تحقق فعلي من المعاملات
- كوبونات خصم
- لوحة إدارة كاملة: إحصائيات، إدارة مستخدمين، إيقاف/حذف قسري للبوتات
- مصادقة ثنائية (2FA / TOTP)، إدارة الجلسات والأجهزة، مفاتيح API
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
git clone <repo-url> wolfhost
cd wolfhost
cp .env.example .env
# عدّل .env وضع القيم الحقيقية (كلمات مرور، مفاتيح API، إلخ)
./scripts/deploy.sh
```

المنصة ستكون متاحة على `https://yourdomain.com` بعد إعداد شهادات SSL في `nginx/certs/`.

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

مزيد من التفاصيل: [الهيكلة المعمارية](docs/ARCHITECTURE.md) · [توثيق الـ API](docs/API.md) · [دليل النشر](docs/DEPLOYMENT.md)

## الترخيص

جميع الحقوق محفوظة — 3MH Technologies | https://3mh.pages.dev/ar/
