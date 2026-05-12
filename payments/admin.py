from django.contrib import admin

from .models import Token, Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("control_number", "user", "meter", "amount", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("control_number", "user__phone_number", "meter__meter_number")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    list_display = ("value", "transaction", "strategy", "delivered_via_sms", "created_at")
    search_fields = ("value", "transaction__control_number")
    readonly_fields = ("id", "created_at")
