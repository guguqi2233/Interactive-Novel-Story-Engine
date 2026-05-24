import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const appSource = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const novelSource = readFileSync(resolve(root, "src", "novelUi.tsx"), "utf8");
const textUtilsSource = readFileSync(resolve(root, "src", "textUtils.ts"), "utf8");
const failures = [];

function requireToken(source, token, label) {
  if (!source.includes(token)) failures.push(`Missing ${label}: ${token}`);
}

for (const token of ["countWordsFast", "for (let index = 0", "inWord"]) {
  requireToken(textUtilsSource, token, "lightweight word count token");
}

for (const token of [
  "debouncedChapterDraftText",
  "chapterCurrentWordCount",
  "chapterWordCountPending",
  "selectedChapterScenes",
  "selectNovelChapter",
  "ChapterListPro"
]) {
  requireToken(appSource, token, "App Novel performance token");
}

for (const token of [
  "export function ChapterListPro",
  "data-windowed-novel-chapters",
  "data-windowed-novel-scenes",
  "visibleScenes",
  "visibleSnapshots",
  "data-windowed-draft-snapshots",
  "orderedSnapshots",
  "scenesByChapterId",
  "characterSummaries",
  "countWordsFast"
]) {
  requireToken(novelSource, token, "Novel UI performance token");
}

for (const stalePattern of [
  "chapterDraftText.split(/\\s+/)",
  "snapshots.map((snapshot)",
  "filtered.map((scene)"
]) {
  if (novelSource.includes(stalePattern) || appSource.includes(stalePattern)) {
    failures.push(`Found stale large-list or word-count pattern: ${stalePattern}`);
  }
}

for (const [label, source] of [
  ["App.tsx", appSource],
  ["novelUi.tsx", novelSource],
  ["textUtils.ts", textUtilsSource]
]) {
  if (/sk-[A-Za-z0-9_-]{20,}/.test(source)) {
    failures.push(`Secret-looking token detected in ${label}.`);
  }
}

if (failures.length) {
  console.error("v3.6 Novel performance check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.6 Novel performance check passed.");
