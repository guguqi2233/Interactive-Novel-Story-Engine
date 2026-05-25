import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const app = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const pkg = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));

const failures = [];

function requireToken(source, token, label = token) {
  if (!source.includes(token)) {
    failures.push(`Missing ${label}: ${token}`);
  }
}

function forbidPattern(source, pattern, label) {
  if (pattern.test(source)) {
    failures.push(`Forbidden ${label}`);
  }
}

const providerStart = app.indexOf("function KeyboardShortcutsProvider");
const providerEnd = app.indexOf("function StudioHome", providerStart);
const providerSource = providerStart >= 0 && providerEnd > providerStart ? app.slice(providerStart, providerEnd) : "";
const focusStart = app.indexOf("function useManagedDialogFocus");
const focusEnd = app.indexOf("function RouteLoadingBoundary", focusStart);
const focusSource = focusStart >= 0 && focusEnd > focusStart ? app.slice(focusStart, focusEnd) : "";
const confirmStart = app.indexOf("function confirmDangerousAction");
const confirmSource = confirmStart >= 0 ? app.slice(confirmStart, confirmStart + 800) : "";

for (const [source, token, label] of [
  [providerSource, "aria-label=\"打开键盘快捷键帮助\"", "Chinese shortcut help launcher aria-label"],
  [providerSource, "data-testid=\"v38-shortcut-help-launcher\"", "shortcut help launcher test id"],
  [providerSource, "data-testid=\"v38-shortcut-help-dialog\"", "shortcut help dialog test id"],
  [providerSource, "role=\"dialog\"", "dialog role"],
  [providerSource, "aria-modal=\"true\"", "modal semantics"],
  [providerSource, "data-focus-return=\"trigger\"", "focus return marker"],
  [providerSource, "data-dangerous-default-focus=\"none\"", "dangerous default focus marker"],
  [providerSource, "if (event.key === \"Escape\")", "Esc closes shortcut dialog"],
  [providerSource, "handleDialogFocusTrap(event, dialogRef.current)", "dialog focus trap"],
  [providerSource, "快捷键只用于本地导航、搜索聚焦和打开帮助", "Chinese shortcut safety copy"],
  [providerSource, "快捷键不会直接触发危险操作", "dangerous shortcut safety copy"],
  [providerSource, "输入框会忽略导航组合键", "IME/input safety copy"],
  [providerSource, "在此设备启用键盘快捷键", "Chinese shortcut toggle label"],
  [app, "保存、apply、导入、删除、恢复仍必须点击明确按钮并确认", "dangerous direct shortcut prevention copy"],
  [focusSource, "returnFocusRef", "dialog focus return ref"],
  [focusSource, "focusElementSafely(returnFocusRef.current)", "dialog returns focus"],
  [confirmSource, "Native confirm provides keyboard navigation without introducing a custom destructive default button.", "dangerous confirm default focus explanation"],
  [confirmSource, "focusElementSafely(returnFocus)", "dangerous confirm returns focus"],
  [app, "setShortcutStatus(shortcutSaveStatusForMode(mode))", "Ctrl/Cmd+S safe status only"],
  [app, "if (editableTarget)", "editable target shortcut guard"],
  [app, "event.key === \"?\"", "question mark opens shortcut help"],
  [app, "setShortcutHelpOpen(true)", "shortcut help opens from keyboard"]
]) {
  requireToken(source, token, label);
}

for (const forbidden of [
  /aria-label=[^\n]*(sk-(?!test|fake|example|redacted)[A-Za-z0-9_-]{8,})/i,
  /aria-label=[^\n]*(Authorization\s*[:=]|Bearer\s+[A-Za-z0-9._-]+)/i,
  /aria-label=[^\n]*(transient_api_key|api_key\s*[:=]|secret_ref\s*[:=])/i,
  /aria-label=[^\n]*(raw_state_delta|npc_secret|hidden_fact_text_visible)/i
]) {
  forbidPattern(app, forbidden, "secret/hidden/debug content in aria-label");
}

if (/Ctrl\/Cmd\+S[\s\S]{0,240}(delete|restore|import|apply|export)\(/i.test(providerSource)) {
  failures.push("Shortcut help area appears to wire Ctrl/Cmd+S to a dangerous operation.");
}

requireToken(pkg.scripts?.["check:v38-keyboard-focus-a11y"] ?? "", "node scripts/check-v38-keyboard-focus-a11y.mjs", "package script");

if (failures.length) {
  console.error("v3.8 Keyboard / Focus / Accessibility UX check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.8 Keyboard / Focus / Accessibility UX check passed.");
