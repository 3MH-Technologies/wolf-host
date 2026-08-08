export type BotStatus = "created" | "installing" | "running" | "stopped" | "crashed" | "deleting" | "error";
export type BotSourceType = "zip" | "single_file" | "git";

export interface Bot {
  id: string;
  owner_id: string;
  name: string;
  slug: string;
  source_type: BotSourceType;
  status: BotStatus;
  entrypoint: string;
  container_name: string;
  env_vars: Record<string, string>;
  cpu_limit: number;
  ram_limit_mb: number;
  disk_limit_mb: number;
  process_limit: number;
  auto_restart: boolean;
  restart_count: number;
  created_at: string;
  last_started_at: string | null;
}

export interface BotStats {
  cpu_percent: number;
  memory_usage_mb: number;
  memory_limit_mb: number;
  memory_percent: number;
  network_rx_bytes: number;
  network_tx_bytes: number;
}

export interface FileEntry {
  name: string;
  is_dir: boolean;
  size: number;
  modified_at: number;
}

export interface Plan {
  id: string;
  tier: "free" | "basic" | "pro" | "enterprise";
  name: string;
  price_monthly: number;
  max_bots: number;
  max_containers: number;
  cpu_limit: number;
  ram_limit_mb: number;
  storage_limit_mb: number;
  bandwidth_limit_mb: number;
  network_access: boolean;
}

export interface UserProfile {
  id: string;
  email: string;
  username: string;
  role: "user" | "admin" | "super_admin";
  totp_enabled: boolean;
  created_at: string;
}
