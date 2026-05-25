import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const appSource = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const pkg = readFileSync(resolve(root, "package.json"), "utf8");
const failures = [];

function requireToken(token, label) {
  const tokens = Array.isArray(token) ? token : [token];
  if (!tokens.some((candidate) => appSource.includes(candidate))) {
    failures.push(`Missing ${label}: ${tokens.join(" | ")}`);
  }
}

for (const [token, label] of [
  ["LOCAL_OPERATION_PROGRESS_STEPS", "shared progress steps constant"],
  ["scanning", "scanning progress step"],
  ["filtering", "filtering progress step"],
  ["validating", "validating progress step"],
  ["packaging", "packaging progress step"],
  ["writing", "writing progress step"],
  ["done", "done progress step"],
  ["LocalLongOperationProgress", "shared backup/diagnostics progress component"],
  ["data-v36-progress-steps", "progress check marker"],
  ["data-v36-progress-excluded-summary", "excluded summary marker"],
  [["cannot cancel safely", "当前不可安全取消"], "safe cancel-disabled wording"],
  [["Long-running status", "长时间本地操作"], "long-running status wording"],
  ["Upload", "upload boundary summary"],
  ["never", "no upload wording"],
  [".env", ".env exclusion"],
  ["API key", "API key exclusion"],
  ["provider secrets", "provider secret exclusion"],
  ["debug", "debug exclusion"],
  ["mature/private", "mature/private exclusion"],
  ["db/log/cache/build outputs", "db/log/cache/build outputs exclusion"],
  ["sanitizeDisplayError(progress.safeError)", "safe progress error rendering"],
  [["Diagnostics progress", "诊断包进度"], "diagnostics progress panel"],
  ["Debug export progress", "debug export progress panel"],
  [["Backup / restore progress", "备份 / 恢复进度"], "backup/restore progress panel"]
]) {
  requireToken(token, label);
}

for (const stalePattern of [
  "function LocalLongOperationProgress({",
  "progress={diagnosticsProgress}",
  "progress={backupProgress}"
]) {
  requireToken(stalePattern, stalePattern);
}

if (/sk-[A-Za-z0-9_-]{20,}/.test(appSource)) {
  failures.push("Secret-looking token detected in App.tsx.");
}

if (/upload(s|ed)?\s+to\s+(cloud|remote|server)/i.test(appSource)) {
  failures.push("Potential online upload wording found in App.tsx.");
}

if (!/"check:v36-backup-diagnostics-progress"/.test(pkg)) {
  failures.push("package.json is missing check:v36-backup-diagnostics-progress.");
}

if (failures.length) {
  console.error("v3.6 Backup/Diagnostics progress check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.6 Backup/Diagnostics progress check passed.");
