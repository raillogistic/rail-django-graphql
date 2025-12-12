"""
BI reporting module integrated with the GraphQL auto schema.

This extension lets us declare reusable datasets, drive rich visualizations, and
manage export jobs (PDF/CSV/JSON) without custom resolvers. Everything is stored
as Django models so the GraphQL generator can expose CRUD plus method mutations
used by the frontend to render tables, charts, and document exports.
"""

from __future__ import annotations

import ast
import logging
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Avg, Count, Max, Min, Q, Sum
from django.utils import timezone

from rail_django_graphql.core.meta import GraphQLMeta as GraphQLMetaBase
from rail_django_graphql.decorators import action_form, confirm_action

logger = logging.getLogger(__name__)


class ReportingError(Exception):
    """Raised when a reporting configuration cannot be executed."""


@dataclass
class FilterSpec:
    """Declarative filter used by the execution engine."""

    field: str
    lookup: str = "exact"
    value: Any = None
    connector: str = "and"


@dataclass
class DimensionSpec:
    """Dimension exposed to the frontend for grouping/pivoting."""

    name: str
    field: str
    label: str = ""
    transform: Optional[str] = None
    help_text: str = ""


@dataclass
class MetricSpec:
    """Numeric metric declared for the dataset."""

    name: str
    field: str
    aggregation: str = "sum"
    label: str = ""
    help_text: str = ""
    format: Optional[str] = None


@dataclass
class ComputedFieldSpec:
    """Client-side computed value derived from dimension/metric columns."""

    name: str
    formula: str
    label: str = ""
    help_text: str = ""


AGGREGATION_MAP = {
    "count": Count,
    "distinct_count": lambda expr: Count(expr, distinct=True),
    "sum": Sum,
    "avg": Avg,
    "min": Min,
    "max": Max,
}

SAFE_EXPR_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Num,
    ast.Constant,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
    ast.Mod,
    ast.USub,
    ast.Load,
    ast.Name,
    ast.Compare,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.BoolOp,
    ast.And,
    ast.Or,
)


def _safe_formula_eval(formula: str, context: Dict[str, Any]) -> Any:
    """Evaluate simple arithmetic/boolean expressions without builtins."""

    try:
        tree = ast.parse(formula, mode="eval")
    except Exception as exc:
        raise ReportingError(f"Expression invalide '{formula}': {exc}") from exc

    for node in ast.walk(tree):
        if not isinstance(node, SAFE_EXPR_NODES):
            raise ReportingError(
                f"Expression non supportee dans '{formula}': {node.__class__.__name__}"
            )
        if isinstance(node, ast.Name) and node.id not in context:
            context[node.id] = 0

    compiled = compile(tree, "<reporting-formula>", "eval")
    return eval(compiled, {"__builtins__": {}}, context)


def _to_filter_list(
    raw_filters: Optional[Iterable[Dict[str, Any]]],
) -> List[FilterSpec]:
    if not raw_filters:
        return []

    normalized: List[FilterSpec] = []
    for item in raw_filters:
        if not isinstance(item, dict):
            continue
        field_name = item.get("field")
        lookup = item.get("lookup") or "exact"
        value = item.get("value")
        connector = item.get("connector") or "and"
        if not field_name:
            continue
        normalized.append(
            FilterSpec(
                field=str(field_name),
                lookup=str(lookup),
                value=value,
                connector=str(connector).lower(),
            )
        )
    return normalized


def _to_ordering(ordering: Optional[Iterable[str]]) -> List[str]:
    if ordering is None:
        return []
    if isinstance(ordering, str):
        ordering = [ordering]
    return [str(value) for value in ordering if value]


class DatasetExecutionEngine:
    """
    Executes a ReportingDataset definition against its underlying model.

    The engine converts JSON definitions (dimensions, metrics, filters, computed
    fields) into QuerySets and serializable payloads used by GraphQL mutations.
    """

    def __init__(self, dataset: "ReportingDataset"):
        self.dataset = dataset
        self.model = self._load_model()
        self.dimensions = self._load_dimensions()
        self.metrics = self._load_metrics()
        self.computed_fields = self._load_computed_fields()

    def _load_model(self) -> models.Model:
        try:
            return apps.get_model(
                self.dataset.source_app_label, self.dataset.source_model
            )
        except LookupError as exc:
            raise ReportingError(
                f"Impossible de trouver le modele {self.dataset.source_app_label}.{self.dataset.source_model}"
            ) from exc

    def _load_dimensions(self) -> List[DimensionSpec]:
        entries = self.dataset.dimensions or []
        parsed: List[DimensionSpec] = []
        for item in entries:
            try:
                parsed.append(
                    DimensionSpec(
                        name=item.get("name") or item.get("field"),
                        field=item.get("field"),
                        label=item.get("label")
                        or item.get("name")
                        or item.get("field"),
                        transform=item.get("transform"),
                        help_text=item.get("help_text", ""),
                    )
                )
            except Exception:
                continue
        return parsed

    def _load_metrics(self) -> List[MetricSpec]:
        entries = self.dataset.metrics or []
        parsed: List[MetricSpec] = []
        for item in entries:
            try:
                parsed.append(
                    MetricSpec(
                        name=item.get("name") or item.get("field"),
                        field=item.get("field"),
                        aggregation=item.get("aggregation") or "sum",
                        label=item.get("label")
                        or item.get("name")
                        or item.get("field"),
                        help_text=item.get("help_text", ""),
                        format=item.get("format"),
                    )
                )
            except Exception:
                continue
        return parsed

    def _load_computed_fields(self) -> List[ComputedFieldSpec]:
        entries = self.dataset.computed_fields or []
        parsed: List[ComputedFieldSpec] = []
        for item in entries:
            name = item.get("name")
            formula = item.get("formula")
            if not name or not formula:
                continue
            parsed.append(
                ComputedFieldSpec(
                    name=name,
                    formula=formula,
                    label=item.get("label") or name,
                    help_text=item.get("help_text", ""),
                )
            )
        return parsed

    def _build_annotations(self) -> Dict[str, Any]:
        annotations: Dict[str, Any] = {}
        for metric in self.metrics:
            agg = AGGREGATION_MAP.get(metric.aggregation, Sum)
            annotations[metric.name] = agg(metric.field)
        return annotations

    def _get_quick_fields(self) -> List[str]:
        meta_quick = (self.dataset.metadata or {}).get("quick_fields") or []
        if meta_quick:
            return [str(field) for field in meta_quick]
        if self.dimensions:
            return [dim.field for dim in self.dimensions[:3]]
        return []

    def _apply_filters(
        self, queryset: models.QuerySet, filters: List[FilterSpec], quick: str
    ) -> models.QuerySet:
        conditions: List[Q] = []
        for spec in filters:
            try:
                lookup = f"{spec.field}__{spec.lookup}"
                conditions.append(Q(**{lookup: spec.value}))
            except Exception as exc:
                logger.warning("Filtre ignore (%s): %s", spec.field, exc)

        quick_fields = self._get_quick_fields()
        if quick and quick_fields:
            quick_q = Q()
            for field_name in quick_fields:
                quick_q |= Q(**{f"{field_name}__icontains": quick})
            conditions.append(quick_q)

        combined: Optional[Q] = None
        for condition in conditions:
            if combined is None:
                combined = condition
                continue
            combined = combined & condition

        return queryset.filter(combined) if combined is not None else queryset

    def _apply_computed_fields(self, rows: List[Dict[str, Any]]) -> None:
        if not self.computed_fields:
            return

        for row in rows:
            context = {key: row.get(key, 0) for key in row.keys()}
            for computed in self.computed_fields:
                try:
                    row[computed.name] = _safe_formula_eval(
                        computed.formula, dict(context)
                    )
                except ReportingError as exc:
                    row[computed.name] = None
                    row.setdefault("_warnings", []).append(str(exc))

    def describe_columns(self) -> List[Dict[str, Any]]:
        columns: List[Dict[str, Any]] = []
        for dim in self.dimensions:
            columns.append(
                {
                    "name": dim.name,
                    "label": dim.label or dim.name,
                    "kind": "dimension",
                    "help_text": dim.help_text,
                }
            )
        for metric in self.metrics:
            columns.append(
                {
                    "name": metric.name,
                    "label": metric.label or metric.name,
                    "kind": "metric",
                    "help_text": metric.help_text,
                    "format": metric.format,
                }
            )
        for computed in self.computed_fields:
            columns.append(
                {
                    "name": computed.name,
                    "label": computed.label or computed.name,
                    "kind": "computed",
                    "help_text": computed.help_text,
                }
            )
        return columns

    def run(
        self,
        *,
        runtime_filters: Optional[List[FilterSpec]] = None,
        limit: Optional[int] = None,
        ordering: Optional[List[str]] = None,
        quick_search: str = "",
    ) -> Dict[str, Any]:
        queryset = self.model.objects.all()
        default_filters = _to_filter_list(self.dataset.default_filters)
        active_filters = default_filters + (runtime_filters or [])
        queryset = self._apply_filters(queryset, active_filters, quick_search)

        dimension_fields = [dim.field for dim in self.dimensions]
        annotations = self._build_annotations()

        if dimension_fields:
            queryset = queryset.values(*dimension_fields)
        elif not annotations:
            fallback_fields = (self.dataset.metadata or {}).get("fields") or ["id"]
            queryset = queryset.values(*fallback_fields)

        if annotations:
            queryset = queryset.annotate(**annotations)

        applied_ordering = _to_ordering(ordering) or _to_ordering(self.dataset.ordering)
        if applied_ordering:
            queryset = queryset.order_by(*applied_ordering)

        if limit:
            queryset = queryset[:limit]

        rows = list(queryset)
        self._apply_computed_fields(rows)

        return {
            "rows": rows,
            "columns": self.describe_columns(),
            "dimensions": [dim.__dict__ for dim in self.dimensions],
            "metrics": [metric.__dict__ for metric in self.metrics],
            "computed_fields": [comp.__dict__ for comp in self.computed_fields],
            "applied_filters": [spec.__dict__ for spec in active_filters],
            "ordering": applied_ordering,
            "limit": limit,
            "source": {
                "app_label": self.dataset.source_app_label,
                "model": self.dataset.source_model,
            },
        }


def _reporting_roles() -> Dict[str, GraphQLMetaBase.Role]:
    return {
        "reporting_admin": GraphQLMetaBase.Role(
            name="reporting_admin",
            description="Administrateur BI (modeles, exports, securite)",
            permissions=[
                "rail_django_graphql.add_reportingdataset",
                "rail_django_graphql.change_reportingdataset",
                "rail_django_graphql.delete_reportingdataset",
                "rail_django_graphql.view_reportingdataset",
            ],
            parent_roles=[],
        ),
        "reporting_author": GraphQLMetaBase.Role(
            name="reporting_author",
            description="Concepteur de rapports (datasets et visuels)",
            permissions=[
                "rail_django_graphql.add_reportingdataset",
                "rail_django_graphql.change_reportingdataset",
                "rail_django_graphql.view_reportingdataset",
                "rail_django_graphql.add_reportingvisualization",
                "rail_django_graphql.change_reportingvisualization",
                "rail_django_graphql.view_reportingvisualization",
            ],
            parent_roles=["reporting_admin"],
        ),
        "reporting_viewer": GraphQLMetaBase.Role(
            name="reporting_viewer",
            description="Consultation des rapports et exports",
            permissions=[
                "rail_django_graphql.view_reportingdataset",
                "rail_django_graphql.view_reportingvisualization",
                "rail_django_graphql.view_reportingreport",
            ],
            parent_roles=["reporting_author"],
        ),
    }


def _reporting_operations() -> Dict[str, GraphQLMetaBase.OperationGuard]:
    return {
        "list": GraphQLMetaBase.OperationGuard(
            name="list",
            roles=["reporting_viewer", "reporting_author", "reporting_admin"],
            permissions=[],
        ),
        "retrieve": GraphQLMetaBase.OperationGuard(
            name="retrieve",
            roles=["reporting_viewer", "reporting_author", "reporting_admin"],
            permissions=[],
        ),
        "create": GraphQLMetaBase.OperationGuard(
            name="create",
            roles=["reporting_author", "reporting_admin"],
            permissions=[],
        ),
        "update": GraphQLMetaBase.OperationGuard(
            name="update",
            roles=["reporting_author", "reporting_admin"],
            permissions=[],
        ),
        "delete": GraphQLMetaBase.OperationGuard(
            name="delete",
            roles=["reporting_admin"],
            permissions=[],
        ),
    }


class ReportingDataset(models.Model):
    """Stores reusable dataset definitions for BI rendering."""

    class SourceKind(models.TextChoices):
        MODEL = "model", "Modele Django"
        SQL = "sql", "SQL"
        GRAPHQL = "graphql", "GraphQL"
        PYTHON = "python", "Python"

    code = models.SlugField(unique=True, max_length=80, verbose_name="Code")
    title = models.CharField(max_length=120, verbose_name="Titre")
    description = models.TextField(blank=True, verbose_name="Description detaillee")
    source_app_label = models.CharField(
        max_length=120, verbose_name="Application source"
    )
    source_model = models.CharField(max_length=120, verbose_name="Modele source")
    source_kind = models.CharField(
        max_length=30,
        choices=SourceKind.choices,
        default=SourceKind.MODEL,
        verbose_name="Type de source",
    )
    default_filters = models.JSONField(
        default=list,
        verbose_name="Filtres par defaut",
        help_text="Liste de filtres {field, lookup, value}.",
    )
    dimensions = models.JSONField(
        default=list,
        verbose_name="Dimensions",
        help_text="Colonnes pour regroupements/axes.",
    )
    metrics = models.JSONField(
        default=list,
        verbose_name="Mesures",
        help_text="Agregations (sum, avg, count...).",
    )
    computed_fields = models.JSONField(
        default=list,
        verbose_name="Champs calcules",
        help_text="Formules basees sur dimensions/mesures.",
    )
    ordering = models.JSONField(
        default=list,
        verbose_name="Tri par defaut",
        help_text="Expressions order_by appliquees lors des executions.",
    )
    preview_limit = models.PositiveIntegerField(
        default=50, verbose_name="Limite apercu"
    )
    metadata = models.JSONField(
        default=dict,
        verbose_name="Metadonnees UI",
        help_text="Sections, quick fields, champs favorises.",
    )
    last_materialized_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Derniere materialisation"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creation")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Mise a jour")

    class Meta:
        app_label = "rail_django_graphql"
        verbose_name = "Jeu de donnees BI"
        verbose_name_plural = "Jeux de donnees BI"
        ordering = ["title", "code"]
        permissions = [
            ("run_dataset_preview", "Peut executer un apercu de dataset"),
            ("materialize_dataset", "Peut materialiser un dataset"),
        ]

    class GraphQLMeta(GraphQLMetaBase):
        filtering = GraphQLMetaBase.Filtering(
            quick=["code", "title", "description"],
            fields={
                "code": GraphQLMetaBase.FilterField(lookups=["icontains", "exact"]),
                "title": GraphQLMetaBase.FilterField(lookups=["icontains"]),
                "source_app_label": GraphQLMetaBase.FilterField(lookups=["exact"]),
                "source_model": GraphQLMetaBase.FilterField(lookups=["exact"]),
            },
        )
        fields = GraphQLMetaBase.Fields(
            read_only=[
                "created_at",
                "updated_at",
                "last_materialized_at",
            ]
        )
        ordering = GraphQLMetaBase.Ordering(
            allowed=["id", "code", "title", "created_at", "updated_at"],
            default=["title"],
        )
        access = GraphQLMetaBase.AccessControl(
            roles=_reporting_roles(),
            operations=_reporting_operations(),
        )

    def __str__(self) -> str:
        return f"{self.title} ({self.code})"

    def clean(self) -> None:
        if not self.source_app_label or not self.source_model:
            raise ValidationError(
                "L application et le modele source sont obligatoires."
            )
        try:
            apps.get_model(self.source_app_label, self.source_model)
        except LookupError:
            raise ValidationError(
                f"Impossible de resoudre {self.source_app_label}.{self.source_model}"
            )

    def build_engine(self) -> DatasetExecutionEngine:
        return DatasetExecutionEngine(self)

    def _runtime_filters(self, filters: Optional[dict]) -> List[FilterSpec]:
        if not filters:
            return []
        if isinstance(filters, dict):
            items = filters.get("items") or filters.get("filters") or []
        else:
            items = filters
        return _to_filter_list(items)

    @action_form(
        title="Previsualiser le dataset",
        description="Execute le dataset avec filtres rapides pour alimenter un tableau ou un graphique.",
        submit_label="Lancer l apercu",
        fields={
            "quick": {"label": "Recherche rapide", "type": "text"},
            "limit": {"label": "Nombre de lignes", "type": "number"},
            "ordering": {
                "label": "Tri",
                "type": "text",
                "help_text": "Expression order_by (ex: -created_at).",
            },
            "filters": {
                "label": "Filtres additionnels",
                "type": "json",
                "help_text": "Liste {field, lookup, value}.",
            },
        },
    )
    def preview(
        self,
        quick: str = "",
        limit: int = 50,
        ordering: str = "",
        filters: Optional[dict] = None,
    ) -> dict:
        engine = self.build_engine()
        runtime_filters = self._runtime_filters(filters)
        result = engine.run(
            runtime_filters=runtime_filters,
            limit=limit or self.preview_limit,
            ordering=_to_ordering(ordering),
            quick_search=quick,
        )
        return result

    @confirm_action(
        title="Materialiser l apercu",
        message="Capture un snapshot pour reutiliser le dataset hors ligne.",
        confirm_label="Materialiser",
        severity="primary",
    )
    def materialize(self) -> bool:
        engine = self.build_engine()
        snapshot = engine.run(limit=self.preview_limit)
        meta = dict(self.metadata or {})
        meta["materialized_snapshot"] = snapshot
        self.metadata = meta
        self.last_materialized_at = timezone.now()
        self.save(update_fields=["metadata", "last_materialized_at", "updated_at"])
        return True


class ReportingVisualization(models.Model):
    """Visualization attached to a dataset (table, chart, KPI, pivot)."""

    class VisualizationKind(models.TextChoices):
        TABLE = "table", "Tableau"
        BAR = "bar", "Histogramme"
        LINE = "line", "Courbe"
        PIE = "pie", "Camembert"
        KPI = "kpi", "Indicateur"
        AREA = "area", "Aire"
        PIVOT = "pivot", "Pivot"
        HEATMAP = "heatmap", "Heatmap"
        PDF = "pdf", "Export PDF"

    dataset = models.ForeignKey(
        ReportingDataset,
        related_name="visualizations",
        on_delete=models.CASCADE,
        verbose_name="Jeu de donnees",
    )
    code = models.SlugField(max_length=80, verbose_name="Code")
    title = models.CharField(max_length=120, verbose_name="Titre")
    description = models.TextField(blank=True, verbose_name="Description")
    kind = models.CharField(
        max_length=30,
        choices=VisualizationKind.choices,
        default=VisualizationKind.TABLE,
        verbose_name="Type",
    )
    config = models.JSONField(
        default=dict,
        verbose_name="Configuration",
        help_text="Axes, colonnes, legende, couleurs.",
    )
    default_filters = models.JSONField(
        default=list,
        verbose_name="Filtres par defaut",
        help_text="Filtres appliques avant l execution.",
    )
    options = models.JSONField(
        default=dict,
        verbose_name="Options UI",
        help_text="Preferences de rendu (theme, animations).",
    )
    is_default = models.BooleanField(
        default=False, verbose_name="Visualisation par defaut"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creation")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Mise a jour")

    class Meta:
        app_label = "rail_django_graphql"
        verbose_name = "Visualisation BI"
        verbose_name_plural = "Visualisations BI"
        ordering = ["dataset__title", "title"]
        unique_together = ("dataset", "code")

    class GraphQLMeta(GraphQLMetaBase):
        filtering = GraphQLMetaBase.Filtering(
            quick=["code", "title", "description"],
            fields={
                "dataset_id": GraphQLMetaBase.FilterField(lookups=["exact"]),
                "kind": GraphQLMetaBase.FilterField(lookups=["exact"]),
            },
        )
        ordering = GraphQLMetaBase.Ordering(
            allowed=["id", "title", "code", "created_at"],
            default=["title"],
        )
        fields = GraphQLMetaBase.Fields(
            read_only=["created_at", "updated_at"],
        )
        access = GraphQLMetaBase.AccessControl(
            roles=_reporting_roles(),
            operations=_reporting_operations(),
        )

    def __str__(self) -> str:
        return f"{self.title} ({self.kind})"

    def _merge_filters(self, runtime_filters: Optional[dict]) -> List[FilterSpec]:
        base = _to_filter_list(self.default_filters)
        merged = base + _to_filter_list(
            runtime_filters.get("filters", runtime_filters) if runtime_filters else []
        )
        return merged

    @action_form(
        title="Rendre la visualisation",
        description="Prepare les donnees et la configuration pour le frontend.",
        submit_label="Executer",
        fields={
            "quick": {"label": "Recherche rapide", "type": "text"},
            "limit": {"label": "Limite", "type": "number"},
            "filters": {"label": "Filtres runtime", "type": "json"},
        },
    )
    def render(
        self,
        quick: str = "",
        limit: int = 200,
        filters: Optional[dict] = None,
    ) -> dict:
        engine = self.dataset.build_engine()
        merged_filters = self._merge_filters(filters)
        payload = engine.run(
            runtime_filters=merged_filters,
            limit=limit or self.dataset.preview_limit,
            quick_search=quick,
        )
        return {
            "visualization": {
                "code": self.code,
                "title": self.title,
                "kind": self.kind,
                "config": self.config,
                "options": self.options,
            },
            "dataset": payload,
        }


class ReportingReport(models.Model):
    """Report container aggregating multiple visualizations."""

    code = models.SlugField(unique=True, max_length=80, verbose_name="Code")
    title = models.CharField(max_length=140, verbose_name="Titre")
    description = models.TextField(blank=True, verbose_name="Description")
    layout = models.JSONField(
        default=list,
        verbose_name="Layout",
        help_text="Disposition des visualisations {visualization_id, position}.",
    )
    filters = models.JSONField(
        default=list,
        verbose_name="Filtres applicables",
        help_text="Filtres globaux appliques a toutes les visualisations.",
    )
    theme = models.CharField(
        max_length=60, default="light", verbose_name="Theme", blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creation")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Mise a jour")
    visualizations = models.ManyToManyField(
        ReportingVisualization,
        through="ReportingReportBlock",
        related_name="reports",
        verbose_name="Visualisations",
    )

    class Meta:
        app_label = "rail_django_graphql"
        verbose_name = "Rapport BI"
        verbose_name_plural = "Rapports BI"
        ordering = ["title"]

    class GraphQLMeta(GraphQLMetaBase):
        filtering = GraphQLMetaBase.Filtering(
            quick=["code", "title", "description"],
        )
        ordering = GraphQLMetaBase.Ordering(
            allowed=["id", "title", "code", "created_at"],
            default=["title"],
        )
        fields = GraphQLMetaBase.Fields(read_only=["created_at", "updated_at"])
        access = GraphQLMetaBase.AccessControl(
            roles=_reporting_roles(),
            operations=_reporting_operations(),
        )

    def __str__(self) -> str:
        return f"{self.title} ({self.code})"

    def _resolved_blocks(self) -> List["ReportingReportBlock"]:
        return list(
            self.blocks.select_related("visualization", "visualization__dataset")
        )

    def _render_visualizations(
        self, quick: str, limit: int, filters: Optional[dict]
    ) -> List[dict]:
        rendered: List[dict] = []
        for block in self._resolved_blocks():
            payload = block.visualization.render(
                quick=quick,
                limit=limit,
                filters=filters,
            )
            rendered.append(
                {
                    "block_id": block.id,
                    "visualization": payload["visualization"],
                    "dataset": payload["dataset"],
                    "layout": block.layout,
                }
            )
        return rendered

    @action_form(
        title="Assembler le rapport",
        description="Retourne toutes les visualisations et le layout pour un rendu unique.",
        submit_label="Construire",
        fields={
            "quick": {"label": "Recherche rapide", "type": "text"},
            "limit": {"label": "Limite par visualisation", "type": "number"},
            "filters": {"label": "Filtres globaux", "type": "json"},
        },
    )
    def build_payload(
        self,
        quick: str = "",
        limit: int = 200,
        filters: Optional[dict] = None,
    ) -> dict:
        visualizations = self._render_visualizations(
            quick=quick, limit=limit, filters=filters
        )
        return {
            "report": {
                "code": self.code,
                "title": self.title,
                "description": self.description,
                "layout": self.layout,
                "theme": self.theme,
            },
            "visualizations": visualizations,
            "filters": self.filters,
        }


class ReportingReportBlock(models.Model):
    """Through table used to assign visualizations to a report with layout hints."""

    report = models.ForeignKey(
        ReportingReport,
        related_name="blocks",
        on_delete=models.CASCADE,
        verbose_name="Rapport",
    )
    visualization = models.ForeignKey(
        ReportingVisualization,
        related_name="blocks",
        on_delete=models.CASCADE,
        verbose_name="Visualisation",
    )
    position = models.PositiveIntegerField(default=1, verbose_name="Position")
    layout = models.JSONField(
        default=dict,
        verbose_name="Layout",
        help_text="Coordonnees (x,y,width,height) pour le frontend.",
    )
    title_override = models.CharField(
        max_length=140, blank=True, verbose_name="Titre alternatif"
    )

    class Meta:
        app_label = "rail_django_graphql"
        verbose_name = "Bloc de rapport"
        verbose_name_plural = "Blocs de rapport"
        ordering = ["position"]
        unique_together = ("report", "visualization")

    class GraphQLMeta(GraphQLMetaBase):
        access = GraphQLMetaBase.AccessControl(
            roles=_reporting_roles(),
            operations=_reporting_operations(),
        )
        ordering = GraphQLMetaBase.Ordering(
            allowed=["id", "position"],
            default=["position"],
        )

    def __str__(self) -> str:
        return f"{self.report.code} -> {self.visualization.code}"


class ReportingExportJob(models.Model):
    """Tracks export runs (PDF/CSV/JSON) for datasets, visualizations or full reports."""

    class ExportStatus(models.TextChoices):
        PENDING = "pending", "En attente"
        RUNNING = "running", "En cours"
        COMPLETED = "completed", "Termine"
        FAILED = "failed", "Echec"

    class ExportFormat(models.TextChoices):
        PDF = "pdf", "PDF"
        CSV = "csv", "CSV"
        JSON = "json", "JSON"
        XLSX = "xlsx", "Excel"

    title = models.CharField(max_length=140, verbose_name="Titre")
    dataset = models.ForeignKey(
        ReportingDataset,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="export_jobs",
        verbose_name="Dataset",
    )
    visualization = models.ForeignKey(
        ReportingVisualization,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="export_jobs",
        verbose_name="Visualisation",
    )
    report = models.ForeignKey(
        ReportingReport,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="export_jobs",
        verbose_name="Rapport",
    )
    format = models.CharField(
        max_length=10,
        choices=ExportFormat.choices,
        default=ExportFormat.PDF,
        verbose_name="Format",
    )
    status = models.CharField(
        max_length=20,
        choices=ExportStatus.choices,
        default=ExportStatus.PENDING,
        verbose_name="Statut",
    )
    filters = models.JSONField(
        default=dict,
        verbose_name="Filtres",
        help_text="Filtres appliques lors de l export.",
    )
    payload = models.JSONField(
        default=dict,
        verbose_name="Payload",
        help_text="Snapshot utilise par le frontend (donnees et layout).",
    )
    error_message = models.TextField(blank=True, verbose_name="Erreur")
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="Debut")
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name="Fin")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creation")

    class Meta:
        app_label = "rail_django_graphql"
        verbose_name = "Export BI"
        verbose_name_plural = "Exports BI"
        ordering = ["-created_at"]

    class GraphQLMeta(GraphQLMetaBase):
        filtering = GraphQLMetaBase.Filtering(
            quick=["title", "status", "format"],
        )
        ordering = GraphQLMetaBase.Ordering(
            allowed=["id", "created_at", "status", "title"],
            default=["-created_at"],
        )
        fields = GraphQLMetaBase.Fields(read_only=["started_at", "finished_at"])
        access = GraphQLMetaBase.AccessControl(
            roles=_reporting_roles(),
            operations=_reporting_operations(),
        )

    def __str__(self) -> str:
        return f"{self.title} ({self.format})"

    def _build_payload(self) -> dict:
        if self.report:
            return self.report.build_payload(quick="", limit=500, filters=self.filters)
        if self.visualization:
            return self.visualization.render(quick="", limit=500, filters=self.filters)
        if self.dataset:
            return self.dataset.preview(
                quick="",
                limit=self.dataset.preview_limit,
                ordering="",
                filters=self.filters,
            )
        raise ReportingError("Aucune cible d export n est renseignee.")

    @confirm_action(
        title="Lancer l export",
        message="Prepare un payload pour PDF/CSV/JSON.",
        confirm_label="Lancer",
        severity="primary",
    )
    def run_export(self) -> bool:
        self.status = self.ExportStatus.RUNNING
        self.started_at = timezone.now()
        self.save(update_fields=["status", "started_at"])
        try:
            self.payload = self._build_payload()
            self.status = self.ExportStatus.COMPLETED
            self.finished_at = timezone.now()
            self.save(update_fields=["payload", "status", "finished_at"])
            return True
        except Exception as exc:  # pragma: no cover - defensive
            self.status = self.ExportStatus.FAILED
            self.error_message = str(exc)
            self.finished_at = timezone.now()
            self.save(
                update_fields=["status", "error_message", "finished_at", "payload"]
            )
            return False


__all__ = [
    "ReportingDataset",
    "ReportingVisualization",
    "ReportingReport",
    "ReportingReportBlock",
    "ReportingExportJob",
    "ReportingError",
    "DatasetExecutionEngine",
]
