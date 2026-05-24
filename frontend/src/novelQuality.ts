import type { NovelChapter, NovelScene } from "./api";

type NovelIssue = {
  severity: "blocker" | "warning" | "notice";
  code: string;
  category: string;
  ref_type: string;
  ref_id: string;
  affected_label: string;
  message: string;
  safe_detail: string;
  suggested_action: string;
};

export function buildNovelQualityIssues(chapters: NovelChapter[], scenes: NovelScene[]): NovelIssue[] {
  const issues: NovelIssue[] = [];
  for (const chapter of chapters) {
    if (!chapter.summary) {
      issues.push({
        severity: "warning",
        code: "missing_chapter_summary",
        category: "continuity",
        ref_type: "chapter",
        ref_id: chapter.chapter_id,
        affected_label: chapter.title,
        message: "Chapter summary is missing.",
        safe_detail: "Chapter has no safe summary for review, export planning, or World Bible cross-checks.",
        suggested_action: "Add a short safe summary before export or World -> Novel import."
      });
    }
    if ((chapter.scene_refs?.length ?? 0) === 0 && scenes.some((scene) => scene.chapter_id === chapter.chapter_id)) {
      issues.push({
        severity: "notice",
        code: "chapter_scene_refs_outdated",
        category: "structure",
        ref_type: "chapter",
        ref_id: chapter.chapter_id,
        affected_label: chapter.title,
        message: "Chapter scene refs may be incomplete.",
        safe_detail: "Scenes exist for this chapter but scene_refs is empty.",
        suggested_action: "Refresh chapter structure links or add scene refs."
      });
    }
  }
  for (const scene of scenes) {
    if (!scene.summary) {
      issues.push({
        severity: "warning",
        code: "missing_scene_summary",
        category: "scene",
        ref_type: "scene",
        ref_id: scene.scene_id,
        affected_label: scene.title,
        message: "Scene summary is missing.",
        safe_detail: "Scene card lacks a safe summary for search, timeline, and export review.",
        suggested_action: "Add a safe one or two sentence scene summary."
      });
    }
  }
  return issues;
}
