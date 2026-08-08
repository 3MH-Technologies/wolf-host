# Wolf Host — Docker Documentation

## الخدمات

| الخدمة | الوصف | المنافذ |
|---|---|---|
| `postgres` | قاعدة البيانات الرئيسية | داخلي فقط |
| `redis` | Cache + Celery broker | داخلي فقط |
| `backend` | FastAPI API + Docker orchestration | داخلي فقط (خلف nginx) |
| `celery_worker` | مهام خلفية (مراقبة البوتات، إلخ) | — |
| `celery_beat` | جدولة المهام الدورية | — |
| `frontend` | Next.js SSR | داخلي فقط (خلف nginx) |
| `nginx` | Reverse Proxy + SSL | 80, 443 |

## الشبكات

- `wolfhost_internal`: شبكة داخلية تربط كل خدمات المنصة ببعضها
- `wolfhost_bots_net`: شبكة معزولة مخصصة فقط لحاويات البوتات، منفصلة تمامًا عن شبكة البنية التحتية

## Volumes

- `postgres_data`: بيانات PostgreSQL
- `redis_data`: بيانات Redis (AOF)
- `bots_storage`: ملفات كل البوتات (مقسّمة حسب `user_id/bot_slug`)

## أوامر مفيدة

```bash
# عرض حالة كل الخدمات
docker compose ps

# متابعة السجلات
docker compose logs -f backend
docker compose logs -f celery_worker

# الدخول إلى shell داخل الباكيند
docker compose exec backend bash

# عرض كل حاويات البوتات المُدارة
docker ps --filter "label=managed-by=wolfhost"

# إعادة تشغيل خدمة واحدة فقط
docker compose restart backend

# تنفيذ migration جديد
docker compose exec backend alembic revision --autogenerate -m "description"
docker compose exec backend alembic upgrade head
```

## أمان حاويات البوتات

كل حاوية بوت تُنشأ بالإعدادات التالية إلزاميًا (`app/services/docker_engine.py`):

```python
security_opt=["no-new-privileges:true"]
cap_drop=["ALL"]
privileged=False
user="1000:1000"
network=settings.DOCKER_NETWORK_NAME  # أو "none" حسب الخطة
pids_limit=<حسب خطة المستخدم>
mem_limit=<حسب خطة المستخدم>
nano_cpus=<حسب خطة المستخدم>
```

لا يوجد Host Mount لأي مسار خارج مجلد البوت نفسه، ولا وصول إلى `/var/run/docker.sock` من داخل حاويات البوتات.
