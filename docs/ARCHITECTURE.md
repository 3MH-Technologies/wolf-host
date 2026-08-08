# Wolf Host — Architecture

## نظرة عامة

Wolf Host عبارة عن نظام موزع بأربع طبقات رئيسية: واجهة أمامية (Next.js)، طبقة API (FastAPI)، طبقة تنسيق الحاويات (Docker Engine)، وطبقة تخزين (PostgreSQL + Redis + Volumes).

```
                        ┌──────────────┐
                        │    Nginx     │  ← SSL termination, rate limiting
                        └──────┬───────┘
                 ┌─────────────┴─────────────┐
                 ▼                           ▼
        ┌─────────────────┐         ┌─────────────────┐
        │  Next.js (SSR)   │         │  FastAPI Backend │
        └─────────────────┘         └────────┬─────────┘
                                              │
                        ┌─────────────────────┼─────────────────────┐
                        ▼                     ▼                     ▼
                ┌──────────────┐    ┌──────────────────┐   ┌──────────────┐
                │  PostgreSQL  │    │  Docker Engine    │   │    Redis     │
                │  (metadata)  │    │  (bot containers)  │   │ (cache/queue)│
                └──────────────┘    └──────────────────┘   └──────────────┘
                                              │
                                     ┌────────┴────────┐
                                     ▼                 ▼
                              ┌───────────┐     ┌───────────┐
                              │  Bot #1    │ ... │  Bot #N    │
                              │  Container │     │  Container │
                              │  (isolated)│     │  (isolated)│
                              └───────────┘     └───────────┘
```

## طبقة عزل البوتات

كل بوت يعمل داخل Container خاص به، وليس هناك أي مشاركة للموارد أو الملفات بين البوتات:

- **Network**: شبكة Bridge معزولة (`wolfhost_bots_net`)، بدون وصول لشبكة الـ Host، وبدون وصول لـ Docker Socket
- **Filesystem**: تركيب Volume خاص فقط بمجلد البوت، بدون أي Host Mounts أخرى
- **Privileges**: `privileged: false`، `cap_drop: ALL`، `no-new-privileges`، مستخدم غير Root (`1000:1000`)
- **الموارد**: حدود CPU (nano_cpus)، RAM (mem_limit + memswap_limit)، عدد العمليات (pids_limit + ulimits)
- **إعادة التشغيل**: مراقبة دورية كل 30 ثانية عبر Celery Beat؛ عند اكتشاف تعطل غير متوقع تتم إعادة الإنشاء تلقائيًا

## تدفق تشغيل بوت جديد

1. المستخدم يرفع الكود (ZIP / ملف واحد / Git URL)
2. `FileManager` يحفظ الملفات في `storage_path` الخاص بالمستخدم مع تحقق من Path Traversal
3. عند الضغط على "تشغيل": `BotService.start_bot` يستدعي `FileManager.detect_requirements()` لاكتشاف المكتبات المطلوبة
4. `DockerEngine.create_and_start` ينشئ Container جديد بالحدود المحددة في خطة المستخدم، وينفذ `pip install` ثم يشغّل نقطة الدخول
5. حالة البوت تُحدَّث في قاعدة البيانات، والسجلات تُتابع مباشرة عبر Server-Sent Events

## طبقة الأمان

- **مصادقة**: JWT (Access 15 دقيقة + Refresh 7 أيام)، تخزين الجلسات في قاعدة البيانات لدعم الإبطال الفوري
- **كلمات المرور**: Argon2
- **2FA**: TOTP متوافق مع Google Authenticator / Authy
- **Rate Limiting**: عبر Redis على مستوى IP، وعلى مستوى Nginx أيضًا
- **Audit Log**: كل عملية حساسة (تسجيل دخول، إنشاء بوت، حذف، دفع) تُسجَّل مع IP وUser-Agent

## طبقة الفوترة

الفواتير مستقلة عن حالة الاشتراك؛ عند تأكيد الدفع (Webhook من Stripe، أو تحقق يدوي من TronGrid/BscScan لعملة USDT) يتم إنشاء `Subscription` جديد وربط الخطة بالمستخدم. الاشتراكات المنتهية تُغلق تلقائيًا عبر مهمة Celery دورية.
