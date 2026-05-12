from rest_framework.routers import DefaultRouter

from .views import MeterViewSet

router = DefaultRouter()
router.register(r"", MeterViewSet, basename="meter")
urlpatterns = router.urls
