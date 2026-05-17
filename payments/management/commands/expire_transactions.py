from django.core.management.base import BaseCommand
from django.utils import timezone

from payments.models import Transaction


class Command(BaseCommand):
    help = "Mark pending transactions past expires_at as expired."

    def handle(self, *args, **options):
        now = timezone.now()
        count = Transaction.objects.filter(
            status=Transaction.Status.PENDING,
            expires_at__lt=now,
        ).update(status=Transaction.Status.EXPIRED, updated_at=now)
        self.stdout.write(f"Expired {count} transaction(s).")
