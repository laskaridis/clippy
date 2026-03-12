from urllib.parse import urlparse

from rest_framework import serializers

from apps.clips.models import Clip, Label


class LabelSerializer(serializers.ModelSerializer):
    clip_count = serializers.SerializerMethodField()

    class Meta:
        model = Label
        fields = [
            "id",
            "name",
            "description",
            "color",
            "clip_count",
        ]

    def get_clip_count(self, obj: Label) -> int:
        # TODO: For now, compute on the fly; can be optimized later.
        return obj.clips.count()


class LabelCreateCommandSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(
        allow_blank=True, allow_null=True, required=False
    )
    color = serializers.CharField(
        allow_blank=True, allow_null=True, required=False, max_length=32
    )

    def create(self, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated:
            raise serializers.ValidationError(
                "Authentication required to create labels"
            )

        return Label.objects.create(user=user, **validated_data)


class LabelUpdateCommandSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=False)
    description = serializers.CharField(
        allow_blank=True, allow_null=True, required=False
    )
    color = serializers.CharField(
        allow_blank=True, allow_null=True, required=False, max_length=32
    )

    def update(self, instance: Label, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance


class ClipSerializer(serializers.ModelSerializer):
    labels = LabelSerializer(many=True, read_only=True)

    class Meta:
        model = Clip
        fields = [
            "id",
            "title",
            "url",
            "domain",
            "raw_content",
            "normalized_text",
            "notes",
            "labels",
            "created_at",
            "updated_at",
        ]


class CreateClipCommandSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, allow_blank=True, required=False)
    url = serializers.URLField(max_length=2048)
    raw_content = serializers.CharField()
    notes = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    labels = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=True
    )

    def validate_raw_content(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("raw_content must not be empty")
        return value

    def create(self, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated:
            raise serializers.ValidationError("Authentication required to create clips")

        label_names = validated_data.pop("labels", []) or []
        raw_content: str = validated_data["raw_content"]
        url: str = validated_data["url"]

        parsed = urlparse(url)
        domain = parsed.hostname or ""

        normalized_text = " ".join(raw_content.split()).lower()

        clip = Clip.objects.create(
            user=user,
            domain=domain,
            normalized_text=normalized_text,
            **validated_data,
        )

        if label_names:
            labels = []
            for name in label_names:
                cleaned_name = name.strip()
                if not cleaned_name:
                    continue
                label, _ = Label.objects.get_or_create(user=user, name=cleaned_name)
                labels.append(label)
            if labels:
                clip.labels.add(*labels)

        return clip


class QuickSearchQuerySerializer(serializers.Serializer):
    q = serializers.CharField(
        min_length=3, max_length=50, trim_whitespace=False, required=True
    )
