from pydantic import BaseModel, Field

from app.engine.content.validator import ValidationIssue, ValidationReport


class ValidationGraphNode(BaseModel):
    id: str
    label: str
    type: str
    severity: str | None = None
    file: str | None = None
    path: str | None = None
    code: str | None = None


class ValidationGraphEdge(BaseModel):
    source: str
    target: str
    type: str
    label: str | None = None


class ValidationGraphIssue(BaseModel):
    id: str
    severity: str
    file: str
    path: str
    code: str
    message: str
    ref_id: str | None = None
    suggestion: str | None = None


class ValidationGraph(BaseModel):
    world_id: str
    nodes: list[ValidationGraphNode] = Field(default_factory=list)
    edges: list[ValidationGraphEdge] = Field(default_factory=list)
    issues: list[ValidationGraphIssue] = Field(default_factory=list)


def build_validation_graph(report: ValidationReport) -> ValidationGraph:
    nodes: dict[str, ValidationGraphNode] = {}
    edges: list[ValidationGraphEdge] = []
    issues: list[ValidationGraphIssue] = []

    for issue_index, issue in enumerate(
        [*report.errors, *report.warnings, *report.suggestions]
    ):
        file_id = f"file:{issue.file}"
        _add_node(
            nodes,
            ValidationGraphNode(
                id=file_id,
                label=issue.file,
                type="file",
                file=issue.file,
            ),
        )

        entity_id = _entity_node_id(issue)
        _add_node(
            nodes,
            ValidationGraphNode(
                id=entity_id,
                label=_entity_label(issue.path),
                type="entity",
                file=issue.file,
                path=issue.path,
            ),
        )
        edges.append(
            ValidationGraphEdge(
                source=file_id,
                target=entity_id,
                type="contains",
            )
        )

        issue_id = f"issue:{issue_index}:{issue.code}:{_safe_fragment(issue.path)}"
        issue_node = ValidationGraphNode(
            id=issue_id,
            label=issue.code,
            type="issue",
            severity=str(issue.severity),
            file=issue.file,
            path=issue.path,
            code=issue.code,
        )
        _add_node(nodes, issue_node)
        edges.append(
            ValidationGraphEdge(
                source=entity_id,
                target=issue_id,
                type=_edge_type_for_issue(issue),
                label=issue.code,
            )
        )

        if issue.ref_id:
            reference_id = f"reference:{_safe_fragment(issue.ref_id)}"
            _add_node(
                nodes,
                ValidationGraphNode(
                    id=reference_id,
                    label=issue.ref_id,
                    type="reference",
                ),
            )
            edges.append(
                ValidationGraphEdge(
                    source=issue_id,
                    target=reference_id,
                    type=_reference_edge_type_for_issue(issue),
                    label=issue.ref_id,
                )
            )

        if issue.code.startswith("schema") or "schema" in issue.code:
            schema_id = f"schema:{issue.file}"
            _add_node(
                nodes,
                ValidationGraphNode(
                    id=schema_id,
                    label=f"{issue.file} schema",
                    type="schema",
                    file=issue.file,
                ),
            )
            edges.append(
                ValidationGraphEdge(
                    source=issue_id,
                    target=schema_id,
                    type="invalid_value",
                    label="schema",
                )
            )

        issues.append(_graph_issue(issue_id, issue))

    return ValidationGraph(
        world_id=report.world_id,
        nodes=sorted(nodes.values(), key=lambda node: (node.type, node.id)),
        edges=edges,
        issues=issues,
    )


def _add_node(nodes: dict[str, ValidationGraphNode], node: ValidationGraphNode) -> None:
    nodes.setdefault(node.id, node)


def _graph_issue(issue_id: str, issue: ValidationIssue) -> ValidationGraphIssue:
    return ValidationGraphIssue(
        id=issue_id,
        severity=str(issue.severity),
        file=issue.file,
        path=issue.path,
        code=issue.code,
        message=issue.message,
        ref_id=issue.ref_id,
        suggestion=issue.suggestion,
    )


def _edge_type_for_issue(issue: ValidationIssue) -> str:
    code = issue.code
    if "missing" in code or "reference" in code:
        return "missing_reference"
    if "visibility" in code or "hidden" in code or "reveals" in code:
        return "visibility_risk"
    if "cycle" in code or "loop" in code:
        return "cycle"
    return "invalid_value" if issue.severity != "suggestion" else "references"


def _reference_edge_type_for_issue(issue: ValidationIssue) -> str:
    if "missing" in issue.code:
        return "missing_reference"
    return "references"


def _entity_node_id(issue: ValidationIssue) -> str:
    return f"entity:{issue.file}:{_safe_fragment(_entity_label(issue.path))}"


def _entity_label(path: str) -> str:
    if ".yaml." in path:
        return path.split(".yaml.", 1)[1]
    return path


def _safe_fragment(value: str) -> str:
    return "".join(character if character.isalnum() or character in {"_", "-", "."} else "_" for character in value)[:120]
