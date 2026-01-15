from django.contrib import admin

from apps.clips.models import Clip, ClipLabel, Label


@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "color")
    list_filter = ("user",)
    search_fields = ("name", "description")


@admin.register(Clip)
class ClipAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "domain", "created_at")
    list_filter = ("user", "domain", "created_at")
    search_fields = ("title", "url", "normalized_text", "notes")
    date_hierarchy = "created_at"


@admin.register(ClipLabel)
class ClipLabelAdmin(admin.ModelAdmin):
    list_display = ("clip", "label")
    list_filter = ("label",)
    search_fields = ("clip__title", "label__name")
