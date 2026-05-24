import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const cssSource = readFileSync(resolve(root, "src", "styles.css"), "utf8");
const pkg = readFileSync(resolve(root, "package.json"), "utf8");
const failures = [];

for (const [token, label] of [
  ["--color-muted: #566575", "stronger muted text token"],
  ["--color-warning: #7c4d00", "stronger warning text token"],
  ["--card-padding: 16px", "shared card padding token"],
  ["--section-gap: 16px", "shared section gap token"],
  ["--badge-min-height: 24px", "shared badge height token"],
  ["--line-readable: 1.55", "readable line-height token"],
  ["v3.6.24 visual comfort polish", "visual comfort polish marker"],
  [".quality-issue-row,", "quality report row polish"],
  [".hidden-leak-issue-row p", "hidden leak report text polish"],
  [".form-editor label", "form label readability"],
  [".compact-list li", "dense list spacing"],
  [".nav-badge,", "badge normalization"],
  ["input::placeholder", "placeholder contrast"],
  ["check:v36-contrast-spacing", "package script"]
]) {
  const source = token === "check:v36-contrast-spacing" ? pkg : cssSource;
  if (!source.includes(token)) failures.push(`Missing ${label}: ${token}`);
}

if (/font-size\s*:\s*[^;]*(vw|vh|vmin|vmax)/i.test(cssSource)) {
  failures.push("Viewport-based font sizing found; v3.6.24 should avoid viewport-scaled text.");
}

if (/--color-muted:\s*#64727f/.test(cssSource)) {
  failures.push("Muted text token still uses the older lower-contrast value.");
}

if (/--color-warning:\s*#9a6700/.test(cssSource)) {
  failures.push("Warning text token still uses the older lower-contrast value.");
}

if (failures.length) {
  console.error("v3.6 Contrast / Font Size / Spacing Polish check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.6 Contrast / Font Size / Spacing Polish check passed.");
