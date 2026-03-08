from __future__ import annotations

from typing import Any, TypedDict
from urllib.parse import quote

from django.core.exceptions import ValidationError
from django.db.models import Count, F, FloatField, Max, Q, Value
from django.db.models.expressions import ExpressionWrapper
from django.db.models.functions import Coalesce, Greatest

from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector, TrigramSimilarity

from apps.clips.models import Clip, Label


MAX_QUICK_SEARCH_LIMIT = 5
TYPE_PRIORITY = {"clip": 0, "label": 1, "website": 2}


class QuickSearchGroups(TypedDict):
    clips: list[dict[str, Any]]
    labels: list[dict[str, Any]]
    websites: list[dict[str, Any]]


class QuickSearchResult(TypedDict):
    query: str
    total: int
    hits: QuickSearchGroups


def quick_search(*, user, query: str, limit: int = MAX_QUICK_SEARCH_LIMIT) -> QuickSearchResult:
    """Return grouped top-N search hits scoped to a user with strict query validation."""
    validated_query = _validate_query(query)
    if limit <= 0:
        return _empty_result(validated_query)

    effective_limit = min(limit, MAX_QUICK_SEARCH_LIMIT)
    candidates = _postgresql_candidates(user=user, query=validated_query, limit=effective_limit)

    selected = sorted(candidates, key=_candidate_sort_key)[:effective_limit]
    hits: QuickSearchGroups = {
        "clips": [],
        "labels": [],
        "websites": [],
    }
    for candidate in selected:
        item = {key: value for key, value in candidate.items() if not key.startswith("_")}
        if candidate["type"] == "clip":
            hits["clips"].append(item)
        elif candidate["type"] == "label":
            hits["labels"].append(item)
        else:
            hits["websites"].append(item)

    return {
        "query": validated_query,
        "total": len(selected),
        "hits": hits,
    }


def _empty_result(query: str) -> QuickSearchResult:
    return {
        "query": query,
        "total": 0,
        "hits": {
            "clips": [],
            "labels": [],
            "websites": [],
        },
    }


def _validate_query(query: str) -> str:
    normalized_query = query or ""
    if len(normalized_query) < 3:
        raise ValidationError("Ensure this field has at least 3 characters.")
    if len(normalized_query) > 50:
        raise ValidationError("Ensure this field has no more than 50 characters.")
    if any(char.isspace() for char in normalized_query):
        raise ValidationError("Whitespace is not allowed.")
    return normalized_query


def _candidate_sort_key(candidate: dict[str, Any]) -> tuple[Any, ...]:
    recency = candidate.get("_recency")
    recency_timestamp = recency.timestamp() if recency is not None else 0.0
    return (
        -float(candidate["score"]),
        TYPE_PRIORITY[candidate["type"]],
        -recency_timestamp,
        candidate.get("_lexical", ""),
        candidate.get("_identity", ""),
    )


def _postgresql_candidates(*, user, query: str, limit: int) -> list[dict[str, Any]]:
    clip_vector = (
        SearchVector("title", weight="A", config="simple")
        + SearchVector("normalized_text", weight="A", config="simple")
        + SearchVector("url", weight="B", config="simple")
    )
    label_vector = SearchVector("name", weight="A", config="simple")
    search_query = SearchQuery(query, search_type="plain", config="simple")

    clip_qs = (
        Clip.objects.filter(user=user)
        .annotate(
            rank=SearchRank(clip_vector, search_query),
            similarity=Greatest(
                TrigramSimilarity("normalized_text", query),
                TrigramSimilarity("title", query),
                TrigramSimilarity("url", query),
            ),
        )
        .annotate(
            score=ExpressionWrapper(
                (Coalesce(F("rank"), Value(0.0)) * Value(0.7))
                + (Coalesce(F("similarity"), Value(0.0)) * Value(0.3)),
                output_field=FloatField(),
            )
        )
        .filter(Q(rank__gt=0) | Q(similarity__gt=0))
        .order_by("-score", "-created_at", "id")
        .values("id", "title", "raw_content", "url", "created_at", "score")[:limit]
    )

    label_qs = (
        Label.objects.filter(user=user)
        .annotate(
            rank=SearchRank(label_vector, search_query),
            similarity=TrigramSimilarity("name", query),
            clip_count=Count("clips", filter=Q(clips__user=user), distinct=True),
            latest_created_at=Max("clips__created_at", filter=Q(clips__user=user)),
        )
        .annotate(
            score=ExpressionWrapper(
                (Coalesce(F("rank"), Value(0.0)) * Value(0.7))
                + (Coalesce(F("similarity"), Value(0.0)) * Value(0.3)),
                output_field=FloatField(),
            )
        )
        .filter(Q(rank__gt=0) | Q(similarity__gt=0))
        .order_by("-score", "name", "id")
        .values("uuid", "name", "clip_count", "latest_created_at", "score")[:limit]
    )

    website_qs = (
        Clip.objects.filter(user=user)
        .values("url")
        .annotate(
            clip_count=Count("id"),
            latest_created_at=Max("created_at"),
            rank=Max(SearchRank(SearchVector("url", config="simple"), search_query)),
            similarity=Max(TrigramSimilarity("url", query)),
        )
        .annotate(
            score=ExpressionWrapper(
                (Coalesce(F("rank"), Value(0.0)) * Value(0.7))
                + (Coalesce(F("similarity"), Value(0.0)) * Value(0.3)),
                output_field=FloatField(),
            )
        )
        .filter(Q(rank__gt=0) | Q(similarity__gt=0))
        .order_by("-score", "-latest_created_at", "url")[:limit]
    )

    candidates: list[dict[str, Any]] = []
    for row in clip_qs:
        candidates.append(
            {
                "type": "clip",
                "score": float(row["score"]),
                "clip_id": str(row["id"]),
                "title": row["title"],
                "snippet": row["raw_content"][:160],
                "url": row["url"],
                "target_url": f"/clips/{row['id']}/",
                "_recency": row["created_at"],
                "_lexical": (row["title"] or "").lower(),
                "_identity": str(row["id"]),
            }
        )

    for row in label_qs:
        candidates.append(
            {
                "type": "label",
                "score": float(row["score"]),
                "label_uuid": str(row["uuid"]),
                "name": row["name"],
                "clip_count": row["clip_count"],
                "target_url": f"/clips?label={row['uuid']}",
                "_recency": row["latest_created_at"],
                "_lexical": row["name"].lower(),
                "_identity": str(row["uuid"]),
            }
        )

    for row in website_qs:
        encoded_url = quote(row["url"], safe="")
        candidates.append(
            {
                "type": "website",
                "score": float(row["score"]),
                "url": row["url"],
                "clip_count": row["clip_count"],
                "target_url": f"/clips?url={encoded_url}",
                "_recency": row["latest_created_at"],
                "_lexical": row["url"].lower(),
                "_identity": row["url"].lower(),
            }
        )

    return candidates
