import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const appSource = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const cssSource = readFileSync(resolve(root, "src", "styles.css"), "utf8");
const pkg = readFileSync(resolve(root, "package.json"), "utf8");
const failures = [];

const shortcutDialogStart = appSource.indexOf("function ShortcutHelpDialog");
const shortcutDialogEnd = appSource.indexOf("function StudioHome", shortcutDialogStart);
const shortcutDialogSource = shortcutDialogStart >= 0 && shortcutDialogEnd > shortcutDialogStart ? appSource.slice(shortcutDialogStart, shortcutDialogEnd) : "";
const confirmStart = appSource.indexOf("function confirmDangerousAction");
const confirmEnd = appSource.indexOf("function ProjectSelectorPanel", confirmStart);
const confirmSource = confirmStart >= 0 && confirmEnd > confirmStart ? appSource.slice(confirmStart, confirmEnd) : "";

if (!shortcutDialogSource) failures.push("ShortcutHelpDialog source slice not found.");
if (!confirmSource) failures.push("confirmDangerousAction source slice not found.");

for (const [token, label] of [
  ["focusElementSafely", "safe focus helper"],
  ["focusElementImmediately", "immediate focus helper"],
  ["focusableElementsIn", "focusable element helper"],
  ["handleDialogFocusTrap", "dialog focus trap helper"],
  ["useManagedDialogFocus", "modal/dialog focus restore hook"],
  ["useStepTitleFocus", "wizard step title focus hook"],
  ["ref={titleRef} tabIndex={-1}", "dialog title focus target"],
  ["ref={stepTitleRef} tabIndex={-1}", "wizard step title focus target"],
  ["Retry loading local UI", "focusable retry action in error state"],
  ["Back to navigation", "focusable back action in error state"],
  ["Native confirm provides keyboard navigation", "confirm keyboard note"],
  ["focusElementSafely(returnFocus)", "confirm return focus"],
  ["handleDialogFocusTrap(event, dialogRef.current)", "dialog keyboard navigation"],
  ["Keyboard shortcuts", "settings focus-related entry"]
]) {
  if (!appSource.includes(token)) failures.push(`Missing ${label}: ${token}`);
}

if (!/window\.confirm\(message\)/.test(confirmSource)) {
  failures.push("Dangerous confirm no longer uses the native keyboard-accessible confirm path.");
}

if (/focus\([^)]*destructive|autoFocus|data-destructive-default/i.test(confirmSource)) {
  failures.push("Dangerous confirm appears to focus a destructive button by default.");
}

if (!/if \(editableTarget\)\s*\{\s*return;\s*\}/m.test(appSource)) {
  failures.push("Keyboard handling no longer protects text/editable inputs.");
}

if (!cssSource.includes("[tabindex=\"-1\"]:focus")) {
  failures.push("Focused programmatic headings do not have visible focus styling.");
}

if (/SafeJSON|<pre>|sk-[A-Za-z0-9_-]{12,}|Authorization\s*[:=]|transient_api_key\s*[:=]/i.test(shortcutDialogSource)) {
  failures.push("Dialog/focus UI appears to render raw JSON, secrets, auth headers, or transient key data.");
}

if (!/"check:v36-focus-management"/.test(pkg)) {
  failures.push("package.json is missing check:v36-focus-management.");
}

if (failures.length) {
  console.error("v3.6 Focus Management check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.6 Focus Management check passed.");
