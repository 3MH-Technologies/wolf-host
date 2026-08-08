# Wolf Host — Deployment Guide

## المتطلبات

- خادم Linux (Ubuntu 22.04+ موصى به) مع Docker وDocker Compose v2
- دومين موجّه إلى IP الخادم (A Record)
- شهادة SSL (Let's Encrypt أو أي مزود آخر)
- 2 vCPU / 4GB RAM كحد أدنى للبداية (يزيد حسب عدد البوتات المستضافة)

## 1. تجهيز الخادم

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
```

## 2. استنساخ المشروع

```bash
git clone <repo-url> wolfhost
cd wolfhost
cp .env.example .env
```

عدّل `.env` وضع:
- `SECRET_KEY`: قيمة عشوائية طويلة (`openssl rand -hex 32`)
- كلمات مرور قوية لـ `POSTGRES_PASSWORD` و`REDIS_PASSWORD`
- بيانات Stripe/PayPal إن رغبت في تفعيلها
- عناوين محافظ USDT (TRC20/BEP20) الخاصة بك
- `ADMIN_EMAIL` و`ADMIN_PASSWORD` لإنشاء حساب المدير الأول تلقائيًا

## 3. شهادات SSL

```bash
mkdir -p nginx/certs
sudo certbot certonly --standalone -d yourdomain.com
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/certs/
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/certs/
```

## 4. النشر

```bash
./scripts/deploy.sh
```

هذا السكريبت يقوم بـ:
1. بناء صور Docker (backend, frontend)
2. تشغيل PostgreSQL وRedis أولًا
3. تنفيذ Alembic migrations
4. تعبئة الخطط الافتراضية وإنشاء حساب المدير
5. تشغيل باقي الخدمات (backend, celery_worker, celery_beat, frontend, nginx)

## 5. التحقق

```bash
./scripts/healthcheck.sh
docker compose ps
docker compose logs -f backend
```

المنصة متاحة الآن على `https://yourdomain.com`.

## التحديثات

```bash
git pull
docker compose build
docker compose run --rm backend alembic upgrade head
docker compose up -d
```

## النسخ الاحتياطي والاستعادة

```bash
./scripts/backup.sh
./scripts/restore.sh backups/db_20260101_120000.sql.gz backups/bots_storage_20260101_120000.tar.gz
```

يُنصَح بجدولة `backup.sh` عبر cron يوميًا:

```bash
0 3 * * * cd /path/to/wolfhost && ./scripts/backup.sh >> /var/log/wolfhost-backup.log 2>&1
```

## تحجيم أفقي (Scaling)

لزيادة قدرة استضافة البوتات:
- زد موارد الخادم (CPU/RAM) — الحد الفعلي هو موارد الـ Host نفسه
- شغّل `celery_worker` بعدة نسخ (`docker compose up -d --scale celery_worker=3`) لتسريع المراقبة عند وجود آلاف البوتات
- انقل PostgreSQL وRedis إلى خدمات مُدارة منفصلة (RDS / ElastiCache أو ما يعادلها) عند التوسع الكبير

## استكشاف الأخطاء الشائعة

| المشكلة | الحل |
|---|---|
| البوتات لا تعمل | تأكد أن `/var/run/docker.sock` مثبّت في backend وcelery_worker |
| فشل رفع الملفات | تحقق من `MAX_UPLOAD_SIZE_MB` في `.env` وحدود `client_max_body_size` في nginx.conf |
| Rate Limiting شديد | عدّل `RATE_LIMIT_PER_MINUTE` في `.env` |
| فشل الاتصال بقاعدة البيانات | تأكد من صحة `POSTGRES_PASSWORD` في كل من `.env` و`docker-compose.yml` |
