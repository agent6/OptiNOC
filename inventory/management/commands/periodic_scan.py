from django.core.management.base import BaseCommand
from inventory.discovery import periodic_scan

class Command(BaseCommand):
    help = "Perform periodic rescan of all known devices"

    def add_arguments(self, parser):
        parser.add_argument('--community', default='public')

    def handle(self, *args, **options):
        community = options['community']
        scanned = periodic_scan(community)
        self.stdout.write(self.style.SUCCESS(f"Scanned {len(scanned)} devices"))
