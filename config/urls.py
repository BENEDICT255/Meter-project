from django.contrib import admin
from django.urls import include, path

from payments.urls import webhook_urlpatterns

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/meters/", include("meters.urls")),
    path("api/transactions/", include("payments.urls")),
    path("api/webhooks/", include((webhook_urlpatterns, "webhooks"), namespace="webhooks")),
]
