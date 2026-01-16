from rest_framework import generics, permissions, status
from rest_framework.response import Response

from apps.clips.models import Clip
from apps.clips.api.serializers import CreateClipCommandSerializer, ClipSerializer
from webclippings.authentication import CsrfExemptSessionAuthentication

class ClipListCreateView(generics.ListCreateAPIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Clip.objects.filter(user=self.request.user)
            .select_related("user")
            .prefetch_related("labels")
        )

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
        return Response(output_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


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
