from __future__ import annotations

from apps.clips.models import Clip, Label


def create_label(*, user, name: str) -> Label:
    return Label.objects.create(user=user, name=name)


def create_clip(*, user, title: str, url: str, raw_content: str) -> Clip:
    return Clip.objects.create(
        user=user,
        title=title,
        url=url,
        domain="example.com",
        raw_content=raw_content,
        normalized_text=raw_content.lower(),
    )
