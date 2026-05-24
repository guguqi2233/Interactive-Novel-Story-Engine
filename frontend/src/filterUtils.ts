import { useEffect, useState } from "react";

const SECRET_LIKE_PATTERNS = [
  /\bsk-[A-Za-z0-9_-]{12,}\b/g,
  /\bBearer\s+[A-Za-z0-9._-]{12,}\b/gi,
  /\b(api[_-]?key|authorization|secret[_-]?ref|transient[_-]?api[_-]?key|provider[_-]?secret)\s*[:=]\s*[^\s,;]+/gi,
  /([?&](?:token|key|secret|access_token)=)[^&#\s]+/gi
];

export function useDebouncedValue<T>(value: T, delayMs = 180): T {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => setDebouncedValue(value), delayMs);
    return () => window.clearTimeout(timeoutId);
  }, [delayMs, value]);

  return debouncedValue;
}

export function normalizeSafeSearchText(value: unknown): string {
  const raw = Array.isArray(value) ? value.join(" ") : String(value ?? "");
  const redacted = SECRET_LIKE_PATTERNS.reduce((current, pattern) => current.replace(pattern, "[redacted]"), raw);
  return redacted.replace(/\s+/g, " ").trim().toLowerCase();
}

export function buildSafeSearchIndex(values: unknown[]): string {
  return normalizeSafeSearchText(values.filter((value) => value !== undefined && value !== null).join(" "));
}

export function safeSearchMatches(index: string, query: string): boolean {
  const normalizedQuery = normalizeSafeSearchText(query);
  return !normalizedQuery || index.includes(normalizedQuery);
}
