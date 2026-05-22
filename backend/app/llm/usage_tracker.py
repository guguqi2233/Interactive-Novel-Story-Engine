from __future__ import annotations

from collections import Counter, deque
from datetime import datetime, timezone
from time import perf_counter
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.llm.provider_base import LLMProvider, SchemaT


class ModelUsageRecord(BaseModel):
    usage_id: str = Field(default_factory=lambda: f"usage-{uuid4().hex}")
    project_id: str = "local_project"
    provider_id: str
    provider_profile_id: str | None = None
    model_id: str
    mode: str = "authoring"
    use_case: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime | None = None
    duration_ms: float
    input_tokens_estimated: int = 0
    output_tokens_estimated: int = 0
    total_tokens_estimated: int = 0
    cost_estimated: float = 0.0
    currency: str = "USD"
    success: bool = True
    error_type: str | None = None
    request_id: str | None = None

    def safe_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


class CostLatencyUseCaseSummary(BaseModel):
    use_case: str
    count: int
    failures: int
    average_latency_ms: float
    latency_p50_ms: float = 0.0
    latency_p95_ms: float = 0.0
    total_input_tokens_estimated: int
    total_output_tokens_estimated: int
    total_cost_estimated: float


class CostLatencyGroupSummary(BaseModel):
    key: str
    count: int
    failures: int
    latency_p50_ms: float = 0.0
    latency_p95_ms: float = 0.0
    total_tokens_estimated: int = 0
    total_cost_estimated: float = 0.0


class CostLatencySummary(BaseModel):
    enabled: bool
    total_calls: int
    successes: int
    failures: int
    error_rate: float
    average_latency_ms: float
    latency_p50_ms: float = 0.0
    latency_p95_ms: float = 0.0
    total_input_tokens_estimated: int
    total_output_tokens_estimated: int
    total_cost_estimated: float
    by_use_case: list[CostLatencyUseCaseSummary] = Field(default_factory=list)
    by_provider: list[CostLatencyGroupSummary] = Field(default_factory=list)
    by_model: list[CostLatencyGroupSummary] = Field(default_factory=list)
    recent_failures: list[ModelUsageRecord] = Field(default_factory=list)


class ModelUsageStore:
    def __init__(self, max_records: int = 1000) -> None:
        self.enabled = False
        self._records: deque[ModelUsageRecord] = deque(maxlen=max_records)

    def record(self, record: ModelUsageRecord) -> None:
        if not self.enabled:
            return
        if record.created_at is None:
            record.created_at = record.started_at
        if record.total_tokens_estimated == 0:
            record.total_tokens_estimated = record.input_tokens_estimated + record.output_tokens_estimated
        self._records.append(record)

    def recent(
        self,
        limit: int = 50,
        *,
        provider_id: str | None = None,
        model_id: str | None = None,
        use_case: str | None = None,
        project_id: str | None = None,
        mode: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[ModelUsageRecord]:
        if limit <= 0:
            return []
        return _filter_records(list(self._records), provider_id=provider_id, model_id=model_id, use_case=use_case, project_id=project_id, mode=mode, since=since, until=until)[-limit:]

    def clear(self) -> None:
        self._records.clear()

    def summary(
        self,
        *,
        provider_id: str | None = None,
        model_id: str | None = None,
        use_case: str | None = None,
        project_id: str | None = None,
        mode: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> CostLatencySummary:
        records = _filter_records(list(self._records), provider_id=provider_id, model_id=model_id, use_case=use_case, project_id=project_id, mode=mode, since=since, until=until)
        total = len(records)
        failures = sum(1 for record in records if not record.success)
        grouped: dict[str, list[ModelUsageRecord]] = {}
        for record in records:
            grouped.setdefault(record.use_case, []).append(record)
        return CostLatencySummary(
            enabled=self.enabled,
            total_calls=total,
            successes=total - failures,
            failures=failures,
            error_rate=round(failures / total, 4) if total else 0.0,
            average_latency_ms=round(sum(record.duration_ms for record in records) / total, 3) if total else 0.0,
            latency_p50_ms=_percentile([record.duration_ms for record in records], 0.5),
            latency_p95_ms=_percentile([record.duration_ms for record in records], 0.95),
            total_input_tokens_estimated=sum(record.input_tokens_estimated for record in records),
            total_output_tokens_estimated=sum(record.output_tokens_estimated for record in records),
            total_cost_estimated=round(sum(record.cost_estimated for record in records), 8),
            by_use_case=[_summarize_use_case(use_case, items) for use_case, items in sorted(grouped.items())],
            by_provider=_summarize_group(records, "provider_id"),
            by_model=_summarize_group(records, "model_id"),
            recent_failures=[record for record in records if not record.success][-10:],
        )

    def by_mode(self, **filters: object) -> list[CostLatencyGroupSummary]:
        return _summarize_group(_filter_records(list(self._records), **filters), "mode")  # type: ignore[arg-type]

    def by_provider(self, **filters: object) -> list[CostLatencyGroupSummary]:
        return _summarize_group(_filter_records(list(self._records), **filters), "provider_id")  # type: ignore[arg-type]


class UsageTrackingProvider(LLMProvider):
    def __init__(
        self,
        provider: LLMProvider,
        *,
        provider_id: str,
        model_id: str,
        store: ModelUsageStore,
        input_cost_per_1k: float = 0.0,
        output_cost_per_1k: float = 0.0,
        project_id: str = "local_project",
        mode: str = "authoring",
        currency: str = "USD",
    ) -> None:
        self._provider = provider
        self._provider_id = provider_id
        self._model_id = model_id
        self._store = store
        self._input_cost_per_1k = input_cost_per_1k
        self._output_cost_per_1k = output_cost_per_1k
        self._project_id = project_id
        self._mode = mode
        self._currency = currency

    def generate_text(self, messages: list[dict[str, str]], temperature: float = 0.7) -> str:
        started_at = datetime.now(timezone.utc)
        started = perf_counter()
        try:
            output = self._provider.generate_text(messages, temperature)
            self._record("generate_text", started_at, started, messages, output, True, None)
            return output
        except Exception as exc:
            self._record("generate_text", started_at, started, messages, "", False, type(exc).__name__)
            raise

    def generate_json(self, messages: list[dict[str, str]], schema: type[SchemaT], temperature: float = 0.2) -> SchemaT:
        started_at = datetime.now(timezone.utc)
        started = perf_counter()
        use_case = f"generate_json:{schema.__name__}"
        try:
            output = self._provider.generate_json(messages, schema, temperature)
            self._record(use_case, started_at, started, messages, output.model_dump_json(), True, None)
            return output
        except Exception as exc:
            self._record(use_case, started_at, started, messages, "", False, type(exc).__name__)
            raise

    def _record(
        self,
        use_case: str,
        started_at: datetime,
        started: float,
        messages: list[dict[str, str]],
        output: str,
        success: bool,
        error_type: str | None,
    ) -> None:
        input_tokens = _estimate_tokens(_message_text(messages))
        output_tokens = _estimate_tokens(output)
        self._store.record(
            ModelUsageRecord(
                project_id=self._project_id,
                provider_id=self._provider_id,
                provider_profile_id=self._provider_id,
                model_id=self._model_id,
                mode=self._mode,
                use_case=use_case,
                started_at=started_at,
                created_at=started_at,
                duration_ms=round((perf_counter() - started) * 1000, 3),
                input_tokens_estimated=input_tokens,
                output_tokens_estimated=output_tokens,
                total_tokens_estimated=input_tokens + output_tokens,
                cost_estimated=_estimate_cost(
                    input_tokens,
                    output_tokens,
                    self._input_cost_per_1k,
                    self._output_cost_per_1k,
                ),
                currency=self._currency,
                success=success,
                error_type=error_type,
            )
        )


_USAGE_STORE = ModelUsageStore()


def get_model_usage_store() -> ModelUsageStore:
    return _USAGE_STORE


def set_usage_tracking_enabled(enabled: bool) -> None:
    _USAGE_STORE.enabled = enabled


def usage_tracking_enabled() -> bool:
    return _USAGE_STORE.enabled


def wrap_provider_for_usage_tracking(
    provider: LLMProvider,
    *,
    provider_id: str,
    model_id: str,
    enabled: bool,
    input_cost_per_1k: float = 0.0,
    output_cost_per_1k: float = 0.0,
    project_id: str = "local_project",
    mode: str = "authoring",
    currency: str = "USD",
) -> LLMProvider:
    set_usage_tracking_enabled(enabled)
    if not enabled:
        return provider
    if isinstance(provider, UsageTrackingProvider):
        return provider
    return UsageTrackingProvider(
        provider,
        provider_id=provider_id,
        model_id=model_id,
        store=get_model_usage_store(),
        input_cost_per_1k=input_cost_per_1k,
        output_cost_per_1k=output_cost_per_1k,
        project_id=project_id,
        mode=mode,
        currency=currency,
    )


def _summarize_use_case(use_case: str, records: list[ModelUsageRecord]) -> CostLatencyUseCaseSummary:
    total = len(records)
    failures = sum(1 for record in records if not record.success)
    return CostLatencyUseCaseSummary(
        use_case=use_case,
        count=total,
        failures=failures,
        average_latency_ms=round(sum(record.duration_ms for record in records) / total, 3) if total else 0.0,
        latency_p50_ms=_percentile([record.duration_ms for record in records], 0.5),
        latency_p95_ms=_percentile([record.duration_ms for record in records], 0.95),
        total_input_tokens_estimated=sum(record.input_tokens_estimated for record in records),
        total_output_tokens_estimated=sum(record.output_tokens_estimated for record in records),
        total_cost_estimated=round(sum(record.cost_estimated for record in records), 8),
    )


def _summarize_group(records: list[ModelUsageRecord], attr: str) -> list[CostLatencyGroupSummary]:
    grouped: dict[str, list[ModelUsageRecord]] = {}
    for record in records:
        grouped.setdefault(str(getattr(record, attr)), []).append(record)
    summaries: list[CostLatencyGroupSummary] = []
    for key, items in sorted(grouped.items()):
        summaries.append(
            CostLatencyGroupSummary(
                key=key,
                count=len(items),
                failures=sum(1 for record in items if not record.success),
                latency_p50_ms=_percentile([record.duration_ms for record in items], 0.5),
                latency_p95_ms=_percentile([record.duration_ms for record in items], 0.95),
                total_tokens_estimated=sum(record.input_tokens_estimated + record.output_tokens_estimated for record in items),
                total_cost_estimated=round(sum(record.cost_estimated for record in items), 8),
            )
        )
    return summaries


def _filter_records(
    records: list[ModelUsageRecord],
    *,
    provider_id: str | None = None,
    model_id: str | None = None,
    use_case: str | None = None,
    project_id: str | None = None,
    mode: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
) -> list[ModelUsageRecord]:
    return [
        record
        for record in records
        if (provider_id is None or record.provider_id == provider_id)
        and (model_id is None or record.model_id == model_id)
        and (use_case is None or record.use_case == use_case)
        and (project_id is None or record.project_id == project_id)
        and (mode is None or record.mode == mode)
        and (since is None or (record.created_at or record.started_at) >= since)
        and (until is None or (record.created_at or record.started_at) <= until)
    ]


def _percentile(values: list[float], quantile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * quantile)))
    return round(ordered[index], 3)


def _message_text(messages: list[dict[str, str]]) -> str:
    return "\n".join(str(message.get("content", "")) for message in messages)


def _estimate_tokens(text: str) -> int:
    if not text:
        return 0
    words = text.split()
    approx_by_chars = max(1, len(text) // 4)
    return max(len(words), approx_by_chars)


def _estimate_cost(input_tokens: int, output_tokens: int, input_per_1k: float, output_per_1k: float) -> float:
    return round((input_tokens / 1000.0) * input_per_1k + (output_tokens / 1000.0) * output_per_1k, 8)
