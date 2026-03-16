from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.clips.models import Clip, Label
from apps.clips.api.serializers import (
    ClipSerializer,
    CreateClipCommandSerializer,
    LabelCreateCommandSerializer,
    LabelSerializer,
    LabelUpdateCommandSerializer,
    QuickSearchQuerySerializer,
)
from apps.clips.filtering import parse_label_slugs
from apps.clips.services import apply_label_and_filter, resolve_selected_labels
from apps.clips.services import quick_search
from webclippings.authentication import CsrfExemptSessionAuthentication


class ClipListCreateView(generics.ListCreateAPIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = (
            Clip.objects.filter(user=self.request.user)
            .select_related("user")
            .prefetch_related("labels")
        )
        selected_label_slugs = parse_label_slugs(
            self.request.query_params.getlist("label")
        )
        selected_labels = resolve_selected_labels(
            user=self.request.user, selected_label_slugs=selected_label_slugs
        )
        queryset = apply_label_and_filter(queryset=queryset, labels=selected_labels)
        url_filter = self.request.query_params.get("url")
        if url_filter:
            queryset = queryset.filter(url=url_filter)
        return queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateClipCommandSerializer
        return ClipSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        clip = serializer.save()
        output_serializer = ClipSerializer(clip, context=self.get_serializer_context())
        headers = self.get_success_headers(output_serializer.data)
        return Response(
            output_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class ClipDetailView(generics.RetrieveDestroyAPIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ClipSerializer

    def get_queryset(self):
        return (
            Clip.objects.filter(user=self.request.user)
            .select_related("user")
            .prefetch_related("labels")
        )


class LabelListCreateView(generics.ListCreateAPIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Label.objects.filter(user=self.request.user).prefetch_related("clips")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return LabelCreateCommandSerializer
        return LabelSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        label = serializer.save()
        output_serializer = LabelSerializer(
            label, context=self.get_serializer_context()
        )
        headers = self.get_success_headers(output_serializer.data)
        return Response(
            output_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class LabelDetailView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LabelSerializer

    def get_queryset(self):
        return Label.objects.filter(user=self.request.user).prefetch_related("clips")

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = LabelUpdateCommandSerializer(
            instance,
            data=request.data,
            partial=True,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        label = serializer.save()
        output_serializer = LabelSerializer(
            label, context=self.get_serializer_context()
        )
        return Response(output_serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):  # explicit alias for clarity
        return self.partial_update(request, *args, **kwargs)


class QuickSearchView(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_authenticate_header(self, request) -> str:
        return "Session"

    def get(self, request, *args, **kwargs):
        serializer = QuickSearchQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        query = serializer.validated_data["q"]

        try:
            result = quick_search(user=request.user, query=query)
        except DjangoValidationError as exc:
            raise ValidationError({"q": exc.messages}) from exc

        return Response(result, status=status.HTTP_200_OK)
