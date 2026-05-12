from django.urls import path

from .views import InitiatePaymentView, PaymentWebhookView


urlpatterns = [
    path("initiate/", InitiatePaymentView.as_view(), name="transactions-initiate"),
]

webhook_urlpatterns = [
    path("payment/", PaymentWebhookView.as_view(), name="webhook-payment"),
]
