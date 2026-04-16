from django.core.management.base import BaseCommand
from django.utils import timezone
from audit.models import AuditLog
from datetime import timedelta


class Command(BaseCommand):
    help = "Remove audit logs older than 1 years"

    def handle(self, *args, **kwargs):
        limit_date = timezone.now() - timedelta(days=365*1)
        deleted, _ = AuditLog.objects.filter(
            timestamp__lt=limit_date
        ).delete()

        self.stdout.write(f"{deleted} registros removidos.")