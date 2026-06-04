from __future__ import annotations

from collections.abc import Iterable

from apps.clips.models import Label


def normalize_label_name(name: str | None) -> str:
    return (name or "").strip()


def normalize_optional_text(value: str | None) -> str | None:
    normalized_value = (value or "").strip()
    return normalized_value or None


def resolve_or_create_labels(*, user, names: Iterable[str]) -> list[Label]:
    labels: list[Label] = []
    for raw_name in names:
        cleaned_name = normalize_label_name(raw_name)
        if not cleaned_name:
            continue
        label, _ = Label.objects.get_or_create(user=user, name=cleaned_name)
        labels.append(label)
    return labels
