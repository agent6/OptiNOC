from django.core.management.base import BaseCommand
from inventory.discovery import discover_network

class Command(BaseCommand):
    help = "Perform initial network discovery starting from a seed IP"

    def add_arguments(self, parser):
        parser.add_argument('seed_ip')
        parser.add_argument('--community', default='public')

    def handle(self, *args, **options):
        seed_ip = options['seed_ip']
        community = options['community']
        visited = discover_network(seed_ip, community)
        self.stdout.write(self.style.SUCCESS(f"Discovered {len(visited)} devices"))
