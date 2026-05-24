import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));

function read(path) {
  return readFileSync(resolve(root, path), "utf8");
}

function assertContains(source, token, label) {
  if (!source.includes(token)) {
    throw new Error(`Missing ${label}: ${token}`);
  }
}

function assertNotContains(source, token, label) {
  if (source.includes(token)) {
    throw new Error(`Unexpected ${label}: ${token}`);
  }
}

const app = read("src/App.tsx");
const boundary = read("src/errorBoundary.tsx");
const styles = read("src/styles.css");
const packageJson = read("package.json");

assertContains(boundary, "export class AppErrorBoundary", "AppErrorBoundary component");
assertContains(boundary, "formatSafeErrorSummary", "safe error formatter");
assertContains(boundary, "getErrorMessageSafe", "API error redaction reuse");
assertContains(boundary, "data-v36-error-boundary=\"safe\"", "safe boundary marker");
assertContains(boundary, "Retry local panel", "retry action");
assertContains(boundary, "Go Home", "go home action");
assertContains(boundary, "Diagnostics remain local-only", "diagnostics hint");
assertContains(boundary, "stack trace redacted", "stack redaction");
assertContains(boundary, "raw[_\\s-]?env", "raw env redaction");
assertContains(boundary, "hidden[_\\s-]?facts?", "hidden fact redaction");
assertContains(boundary, "sensitive local path", "sensitive path copy");
assertNotContains(boundary, "error.stack", "raw stack access");
assertNotContains(boundary, "<pre", "raw preformatted error rendering");

assertContains(app, "import { AppErrorBoundary } from \"./errorBoundary\";", "AppErrorBoundary import");
assertContains(app, "<AppErrorBoundary key={label}", "route-level AppErrorBoundary use");
assertContains(app, "onGoHome={() => setMode(\"studio\")}", "route go-home recovery");
assertContains(app, "label=\"QA / Debug / Replay\"", "QA/Debug boundary label");
assertContains(app, "setDebugOpen(false);", "debug drawer recovery");

for (const routeLabel of [
  "Project / Novel / Tavern Studio",
  "World Studio",
  "Authoring / Mod Studio",
  "Provider Connectivity",
  "Desktop / Quality / Diagnostics"
]) {
  assertContains(app, routeLabel, `${routeLabel} route label`);
}

assertContains(styles, ".app-error-boundary", "error boundary styling");
assertContains(packageJson, "\"check:v36-error-boundary\"", "package script");

console.log("v3.6 error boundary check passed.");
