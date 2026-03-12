import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Label(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4, unique=True, editable=False, db_index=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="labels"
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    color = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "name"], name="uniq_label_name_per_user"
            ),
        ]

    def __str__(self) -> str:  # pragma: no cover - simple repr
        return self.name


class Clip(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="clips"
    )
    title = models.CharField(max_length=255, blank=True)
    url = models.URLField(max_length=2048)
    domain = models.CharField(max_length=255)
    raw_content = models.TextField()
    normalized_text = models.TextField()
    notes = models.TextField(blank=True, null=True)
    labels = models.ManyToManyField(Label, through="ClipLabel", related_name="clips")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["user", "domain"]),
            models.Index(fields=["user", "url"], name="clips_clip_user_id_3effdd_idx"),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover - simple repr
        return self.title or str(self.id)


class ClipLabel(models.Model):
    clip = models.ForeignKey(Clip, on_delete=models.CASCADE)
    label = models.ForeignKey(Label, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["clip", "label"], name="uniq_clip_label"),
        ]

    def clean(self) -> None:
        if self.clip and self.label and self.clip.user_id != self.label.user_id:
            raise ValidationError("Clip and Label must belong to the same user")

    def save(self, *args, **kwargs):  # pragma: no cover - delegates to clean
        self.full_clean()
        return super().save(*args, **kwargs)
