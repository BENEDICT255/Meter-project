from rest_framework import mixins, viewsets

from .models import Meter
from .serializers import MeterSerializer


class MeterViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = MeterSerializer

    def get_queryset(self):
        return Meter.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
