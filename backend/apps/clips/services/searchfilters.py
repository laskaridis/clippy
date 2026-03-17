from __future__ import annotations

from typing import TypedDict

from django.db.models import Count, Q, QuerySet

from apps.clips.models import Clip, Label


class WebLabelFilterItem(TypedDict):
    name: str
    slug: str
    color: str | None
    contextual_results_count: int


def resolve_selected_labels(*, user, selected_label_slugs: list[str]) -> list[Label]:
    """Resolve selected labels by slug preserving input order and valid ownership."""
    if not selected_label_slugs:
        return []
    labels = Label.objects.filter(user=user, slug__in=selected_label_slugs).only(
        "id", "name", "slug", "color"
    )
    labels_by_slug: dict[str, Label] = {label.slug: label for label in labels}
    return [
        labels_by_slug[slug] for slug in selected_label_slugs if slug in labels_by_slug
    ]


def apply_label_and_filter(
    *, queryset: QuerySet[Clip], labels: list[Label]
) -> QuerySet[Clip]:
    """
    Apply selected label filters to the given clips queryset (using AND logic across multiple labels).
    Parameters:
    - ``queryset``: The base queryset of clips to filter. This should already be scoped to the relevant user.
    - ``labels``: A list of Label instances that represent the currently selected label filters.
    """
    for label in labels:
        queryset = queryset.filter(labels__id=label.id)
    return queryset.distinct()


def annotate_contextual_label_counts(
    *, user, filtered_clips_queryset: QuerySet[Clip]
) -> QuerySet[Label]:
    """
    Returns a list of all user's labels annotated with the count of matching results after applying the
    selected filters.
    """
    return (
        Label.objects.filter(user=user)
        .annotate(
            contextual_results_count=Count(
                "clips",
                filter=Q(clips__id__in=filtered_clips_queryset.values("id")),
                distinct=True,  # defensive: not needed because a unique constraint at the join table
            )
        )
        .order_by("name")
    )


def build_web_label_filters_dataset(
    *,
    user,
    selected_label_slugs: list[str],
) -> list[WebLabelFilterItem]:
    """Return flat web label dataset with contextual counts for the current selection."""
    selected_labels: list[Label] = resolve_selected_labels(
        user=user, selected_label_slugs=selected_label_slugs
    )

    filtered_clips_queryset: QuerySet[Clip] = apply_label_and_filter(
        queryset=Clip.objects.filter(user=user),
        labels=selected_labels,
    )

    labels_queryset: QuerySet[Label] = annotate_contextual_label_counts(
        user=user,
        filtered_clips_queryset=filtered_clips_queryset,
    )

    return [
        {
            "name": label.name,
            "slug": label.slug,
            "color": label.color,
            "contextual_results_count": int(
                getattr(label, "contextual_results_count", 0)
            ),
        }
        for label in labels_queryset
    ]
