export type SafeApiCacheScope =
  | "provider"
  | "quality"
  | "eventlog"
  | "timeline"
  | "module-browser";

export type SafeApiCacheStatus = {
  key: string;
  label: string;
  scope: SafeApiCacheScope;
  updatedAt: string;
  staleAt: string;
  stale: boolean;
  failed: boolean;
  safeError?: string;
  summary: string;
  itemCount?: number;
};

export type SafeApiCacheEntry<T> = SafeApiCacheStatus & {
  value: T;
};

type StoredSafeApiCacheEntry = SafeApiCacheEntry<unknown> & {
  staleAfterMs: number;
};

type WriteSafeApiCacheOptions = {
  staleAfterMs?: number;
  summary?: string;
  itemCount?: number;
};

const DEFAULT_SAFE_CACHE_TTL_MS = 5 * 60 * 1000;
const safeApiCacheStore = new Map<string, StoredSafeApiCacheEntry>();

const unsafeCachePayloadPatterns: RegExp[] = [
  /sk-[A-Za-z0-9_-]{12,}/i,
  /authorization\s*[:=]\s*(bearer\s+)?[A-Za-z0-9._~+/=-]+/i,
  /"(?:transient[_-]?)?api[_-]?key"\s*:\s*"[^"]+"/i,
  /"(?:provider[_-]?secret|secret[_-]?ref|relay[_-]?token|access[_-]?token|password|token)"\s*:\s*"[^"]+"/i,
  /raw[_-]?env/i,
  /raw[_-]?provider[_-]?(?:response|error)/i,
  /authorization[_-]?header/i,
  /raw[_-]?prompt/i,
  /raw[_-]?output/i,
  /hidden[_-]?facts?/i,
  /npc[_-]?secrets?/i,
  /npc[_-]?knowledge/i,
  /raw[_-]?state[_-]?deltas?/i,
  /raw[_-]?game[_-]?state/i,
  /mature[_-]?private/i,
  /debug[_-]?memory/i
];

export function writeSafeApiCache<T>(
  key: string,
  label: string,
  scope: SafeApiCacheScope,
  value: T,
  options: WriteSafeApiCacheOptions = {}
): SafeApiCacheStatus {
  const now = new Date();
  const staleAfterMs = options.staleAfterMs ?? DEFAULT_SAFE_CACHE_TTL_MS;
  const serialized = safeStringify(value);
  if (containsUnsafeCachePayload(serialized)) {
    return markSafeApiCacheFailed(
      key,
      label,
      scope,
      "Unsafe cache payload rejected before storage.",
      options
    );
  }

  const status: StoredSafeApiCacheEntry = {
    key,
    label,
    scope,
    value,
    updatedAt: now.toISOString(),
    staleAt: new Date(now.getTime() + staleAfterMs).toISOString(),
    stale: false,
    failed: false,
    summary: sanitizeCacheText(options.summary ?? summarizeSafeValue(value)),
    itemCount: options.itemCount,
    staleAfterMs
  };
  safeApiCacheStore.set(key, status);
  return toPublicStatus(status);
}

export function readSafeApiCache<T>(key: string): SafeApiCacheEntry<T> | null {
  const entry = safeApiCacheStore.get(key);
  if (!entry) {
    return null;
  }
  return { ...toPublicStatus(entry), value: entry.value as T };
}

export function markSafeApiCacheFailed(
  key: string,
  label: string,
  scope: SafeApiCacheScope,
  error: unknown,
  options: WriteSafeApiCacheOptions = {}
): SafeApiCacheStatus {
  const now = new Date();
  const staleAfterMs = options.staleAfterMs ?? DEFAULT_SAFE_CACHE_TTL_MS;
  const safeError = sanitizeCacheText(error instanceof Error ? error.message : String(error || "Refresh failed."));
  const entry: StoredSafeApiCacheEntry = {
    key,
    label,
    scope,
    value: {
      failed: true,
      safeError
    },
    updatedAt: now.toISOString(),
    staleAt: now.toISOString(),
    stale: true,
    failed: true,
    safeError,
    summary: sanitizeCacheText(options.summary ?? "Last refresh failed; cached value was not updated."),
    itemCount: options.itemCount,
    staleAfterMs
  };
  safeApiCacheStore.set(key, entry);
  return toPublicStatus(entry);
}

export function getSafeApiCacheStatuses(): SafeApiCacheStatus[] {
  const nowMs = Date.now();
  return Array.from(safeApiCacheStore.values())
    .map((entry) => toPublicStatus(entry, nowMs))
    .sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
}

export function clearSafeApiCacheKey(key: string): void {
  safeApiCacheStore.delete(key);
}

export function containsUnsafeCachePayload(serialized: string): boolean {
  return unsafeCachePayloadPatterns.some((pattern) => pattern.test(serialized));
}

function toPublicStatus(entry: StoredSafeApiCacheEntry, nowMs = Date.now()): SafeApiCacheStatus {
  const stale = entry.failed || new Date(entry.staleAt).getTime() <= nowMs;
  return {
    key: entry.key,
    label: entry.label,
    scope: entry.scope,
    updatedAt: entry.updatedAt,
    staleAt: entry.staleAt,
    stale,
    failed: entry.failed,
    safeError: entry.safeError,
    summary: sanitizeCacheText(entry.summary),
    itemCount: entry.itemCount
  };
}

function summarizeSafeValue(value: unknown): string {
  if (Array.isArray(value)) {
    return `${value.length} safe summary item(s) cached.`;
  }
  if (!value || typeof value !== "object") {
    return "Safe summary cached.";
  }
  const record = value as Record<string, unknown>;
  const status = typeof record.status === "string" ? record.status : "";
  const countFields = ["count", "item_count", "event_count", "model_count", "package_count"]
    .map((field) => (typeof record[field] === "number" ? `${field}: ${record[field]}` : ""))
    .filter(Boolean);
  return [status, ...countFields].filter(Boolean).join("; ") || "Safe summary cached.";
}

function safeStringify(value: unknown): string {
  try {
    return JSON.stringify(value) ?? "";
  } catch {
    return "[unserializable safe cache payload]";
  }
}

function sanitizeCacheText(value: string): string {
  return value
    .replace(/sk-[A-Za-z0-9_-]+/g, "sk-[redacted]")
    .replace(/authorization\s*[:=]\s*(bearer\s+)?[A-Za-z0-9._~+/=-]+/gi, "[redacted authorization]")
    .replace(/((?:transient[_-]?)?api[_-]?key|secret[_-]?ref|provider[_-]?secret|relay[_-]?token|access[_-]?token|secret|token|password)\s*[:=]\s*['"]?[^'",\s}\]]+/gi, "$1=[redacted]")
    .replace(/([?&](?:api[_-]?key|key|token|access[_-]?token|secret|signature|sig|auth|authorization)=)[^&#\s"'<>]+/gi, "$1[redacted]")
    .replace(/(\/(?:token|tokens|key|keys|secret|secrets|bearer|auth)\/)[A-Za-z0-9._~+/=-]{8,}/gi, "$1[redacted]")
    .replace(/(raw[_\s-]?provider[_\s-]?(?:error|response)|provider[_\s-]?raw[_\s-]?response|raw[_\s-]?response)\s*[:=]\s*[^}\n]+/gi, "[redacted provider response]")
    .replace(/[A-Z]:\\[^\s"'<>]+/g, "[local path redacted]")
    .replace(/\/[^\s"'<>]*(?:\.env|\.db|\.sqlite|logs?|cache|backups?|crash-reports|node_modules|dist)[^\s"'<>]*/gi, "[local path redacted]")
    .replace(/(hidden[_\s-]?facts?|npc[_\s-]?secrets?|raw[_\s-]?prompts?|raw[_\s-]?outputs?|state[_\s-]?deltas?)\s*[:=]\s*[^}\n]+/gi, "$1=[redacted]")
    .replace(/Traceback[\s\S]*/i, "[stack trace redacted]");
}
