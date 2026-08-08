# Wolf Host — ER Diagram

```
users
├── id (PK, UUID)
├── email (unique)
├── username (unique)
├── hashed_password
├── role (enum: user/admin/super_admin)
├── totp_secret / totp_enabled
├── plan_id (FK → plans.id, nullable)
└── is_active / is_suspended

user_sessions
├── id (PK)
├── user_id (FK → users.id)
├── refresh_token_hash
├── ip_address / user_agent / device_label
└── is_revoked / expires_at

api_keys
├── id (PK)
├── user_id (FK → users.id)
├── key_prefix / key_hash
└── is_active

bots
├── id (PK)
├── owner_id (FK → users.id)
├── name / slug (unique)
├── source_type (enum: zip/single_file/git)
├── status (enum: created/installing/running/stopped/crashed/deleting/error)
├── container_name (unique) / container_id
├── storage_path
├── env_vars (JSONB)
├── cpu_limit / ram_limit_mb / disk_limit_mb / process_limit
└── auto_restart / restart_count

plans
├── id (PK)
├── tier (enum: free/basic/pro/enterprise, unique)
├── price_monthly
├── max_bots / max_containers
└── cpu_limit / ram_limit_mb / storage_limit_mb / bandwidth_limit_mb

subscriptions
├── id (PK)
├── user_id (FK → users.id)
├── plan_id (FK → plans.id)
├── status (enum: active/expired/cancelled/pending)
└── starts_at / ends_at / auto_renew

invoices
├── id (PK)
├── user_id (FK → users.id)
├── plan_id (FK → plans.id)
├── provider (enum: stripe/paypal/usdt_trc20/usdt_bep20)
├── status (enum: pending/paid/failed/expired/refunded)
├── amount / currency
├── crypto_address / crypto_tx_hash
└── expires_at / paid_at

coupons
├── id (PK)
├── code (unique)
├── discount_percent
└── max_uses / used_count

audit_logs
├── id (PK)
├── user_id (FK → users.id, nullable)
├── action / resource_type / resource_id
├── ip_address / user_agent
└── metadata_json (JSONB)

notifications
├── id (PK)
├── user_id (FK → users.id)
├── title / message
└── is_read
```

## العلاقات

- `users` 1─N `bots` (حذف تسلسلي: حذف المستخدم يحذف بوتاته)
- `users` 1─N `user_sessions`, `api_keys`
- `users` 1─N `subscriptions`, `invoices`
- `plans` 1─N `subscriptions`, `invoices`
- `users` 1─N `audit_logs` (SET NULL عند حذف المستخدم للحفاظ على السجل)
