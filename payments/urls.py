from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import InitiatePaymentView, PaymentWebhookView, TransactionViewSet


router = DefaultRouter()
router.register(r"", TransactionViewSet, basename="transaction")

urlpatterns = [
    path("initiate/", InitiatePaymentView.as_view(), name="transactions-initiate"),
    *router.urls,
]

webhook_urlpatterns = [
    path("payment/", PaymentWebhookView.as_view(), name="webhook-payment"),
]
