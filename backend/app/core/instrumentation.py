from collections import defaultdict, deque
from contextlib import contextmanager
from datetime import datetime, timezone
from time import perf_counter
from typing import Iterator
from uuid import uuid4

from pydantic import BaseModel, Field


class PerformanceSample(BaseModel):
    sample_id: str = Field(default_factory=lambda: f"perf-{uuid4().hex}")
    name: str
    duration_ms: float
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    stage_durations_ms: dict[str, float] = Field(default_factory=dict)
    tags: dict[str, str] = Field(default_factory=dict)


class PerformanceSummaryEntry(BaseModel):
    name: str
    count: int
    total_duration_ms: float
    average_duration_ms: float
    max_duration_ms: float


class PerformanceSummary(BaseModel):
    enabled: bool
    sample_count: int
    entries: list[PerformanceSummaryEntry] = Field(default_factory=list)


class PerformanceRecorder:
    def __init__(self, max_samples: int = 500) -> None:
        self._samples: deque[PerformanceSample] = deque(maxlen=max_samples)
        self.enabled = False

    def record(self, sample: PerformanceSample) -> None:
        if not self.enabled:
            return
        self._samples.append(_sanitize_sample(sample))

    def recent(self, limit: int = 50) -> list[PerformanceSample]:
        if limit <= 0:
            return []
        return list(self._samples)[-limit:]

    def clear(self) -> None:
        self._samples.clear()

    def summary(self) -> PerformanceSummary:
        grouped: dict[str, list[PerformanceSample]] = defaultdict(list)
        for sample in self._samples:
            grouped[sample.name].append(sample)
        entries = []
        for name, samples in sorted(grouped.items()):
            total = sum(sample.duration_ms for sample in samples)
            entries.append(
                PerformanceSummaryEntry(
                    name=name,
                    count=len(samples),
                    total_duration_ms=round(total, 3),
                    average_duration_ms=round(total / len(samples), 3),
                    max_duration_ms=round(max(sample.duration_ms for sample in samples), 3),
                )
            )
        return PerformanceSummary(
            enabled=self.enabled,
            sample_count=len(self._samples),
            entries=entries,
        )


class PerformanceSpan:
    def __init__(self, name: str, tags: dict[str, str] | None = None) -> None:
        self.name = name
        self.tags = tags or {}
        self.stage_durations_ms: dict[str, float] = {}
        self._started_at = datetime.now(timezone.utc)
        self._start = perf_counter()

    @contextmanager
    def stage(self, name: str) -> Iterator[None]:
        stage_start = perf_counter()
        try:
            yield
        finally:
            duration = (perf_counter() - stage_start) * 1000
            self.stage_durations_ms[name] = round(
                self.stage_durations_ms.get(name, 0.0) + duration,
                3,
            )

    def finish(self, tags: dict[str, str] | None = None) -> PerformanceSample:
        merged_tags = {**self.tags, **(tags or {})}
        return PerformanceSample(
            name=self.name,
            duration_ms=round((perf_counter() - self._start) * 1000, 3),
            started_at=self._started_at,
            stage_durations_ms=self.stage_durations_ms,
            tags=merged_tags,
        )


_RECORDER = PerformanceRecorder()


def get_performance_recorder() -> PerformanceRecorder:
    return _RECORDER


def set_performance_logging_enabled(enabled: bool) -> None:
    _RECORDER.enabled = enabled


def performance_logging_enabled() -> bool:
    return _RECORDER.enabled


@contextmanager
def timed_sample(name: str, tags: dict[str, str] | None = None) -> Iterator[PerformanceSpan]:
    span = PerformanceSpan(name=name, tags=tags)
    try:
        yield span
    finally:
        get_performance_recorder().record(span.finish())


def record_performance_sample(
    name: str,
    duration_ms: float,
    stage_durations_ms: dict[str, float] | None = None,
    tags: dict[str, str] | None = None,
) -> None:
    get_performance_recorder().record(
        PerformanceSample(
            name=name,
            duration_ms=round(duration_ms, 3),
            stage_durations_ms=stage_durations_ms or {},
            tags=tags or {},
        )
    )


def _sanitize_sample(sample: PerformanceSample) -> PerformanceSample:
    safe_tags = {
        key: value
        for key, value in sample.tags.items()
        if _safe_tag(key, value)
    }
    return sample.model_copy(update={"tags": safe_tags})


def _safe_tag(key: str, value: str) -> bool:
    lowered = f"{key}={value}".lower()
    forbidden = ["api_key", "llm_api_key", "secret", "sk-", "prompt", "game_state", "state_delta"]
    return not any(term in lowered for term in forbidden)
