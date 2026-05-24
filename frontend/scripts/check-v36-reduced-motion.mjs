import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const appSource = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const cssSource = readFileSync(resolve(root, "src", "styles.css"), "utf8");
const pkg = readFileSync(resolve(root, "package.json"), "utf8");
const failures = [];

for (const [token, label] of [
  ["REDUCED_MOTION_PREF_KEY", "local reduced-motion preference key"],
  ["systemPrefersReducedMotion", "prefers-reduced-motion detector"],
  ["reducedMotionInitialEnabled", "initial reduced-motion preference"],
  ["reducedMotionEnabled", "reduced-motion React state"],
  ["document.documentElement.dataset.reducedMotion", "document reduced-motion token"],
  ["reduced-motion-preference", "document reduced-motion class"],
  ["reduced-motion-root", "root reduced-motion class"],
  ["data-reduced-motion={reducedMotionEnabled ? \"enabled\" : \"disabled\"}", "root reduced-motion data marker"],
  ["Reduce non-essential motion", "Settings reduced-motion toggle"],
  ["onToggleReducedMotion", "Settings reduced-motion callback"],
  ["motionSafeScrollBehavior()", "motion-safe scroll behavior"],
  ["const replayAdvanceMs = reducedMotionActive() ? 2200 : 1200", "replay simplified cadence"],
  ["@media (prefers-reduced-motion: reduce)", "system reduced-motion CSS"],
  ["animation-duration: 0.01ms !important", "animation reduction CSS"],
  ["transition-duration: 0.01ms !important", "transition reduction CSS"],
  ["scroll-behavior: auto !important", "smooth scroll reduction CSS"],
  ["[tabindex=\"-1\"]:focus", "focus outline remains defined"],
  ["check:v36-reduced-motion", "package script"]
]) {
  const source = token.startsWith("@media") || token.includes("duration") || token.includes("scroll-behavior") || token.includes("[tabindex")
    ? cssSource
    : token === "check:v36-reduced-motion"
      ? pkg
      : appSource;
  if (!source.includes(token)) failures.push(`Missing ${label}: ${token}`);
}

if (/reducedMotion|reduced-motion/i.test(appSource) && /sk-[A-Za-z0-9_-]{8,}|Authorization\s*[:=]|transient_api_key\s*[:=]|secret_ref\s*[:=]/i.test(appSource.slice(appSource.indexOf("REDUCED_MOTION_PREF_KEY"), appSource.indexOf("function isEditableShortcutTarget")))) {
  failures.push("Reduced-motion preference setup appears to include secret-like data.");
}

if (/setReducedMotionEnabled[\s\S]{0,220}(handleCreateBackup|handleApplyMigration|handleCreateDiagnosticsBundle|handleDeleteSave|handleSubmit)/.test(appSource)) {
  failures.push("Reduced-motion toggle appears to trigger a business or dangerous action.");
}

if (failures.length) {
  console.error("v3.6 Reduced Motion / Visual Comfort check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.6 Reduced Motion / Visual Comfort check passed.");
