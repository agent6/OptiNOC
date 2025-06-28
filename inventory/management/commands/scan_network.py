from django.core.management.base import BaseCommand
from inventory.discovery import discover_network, periodic_scan


class Command(BaseCommand):
    help = (
        "Run a network scan. If --seed is provided, perform initial discovery "
        "starting from that IP. Otherwise rescan all known devices."
    )

    def add_arguments(self, parser):
        parser.add_argument('--seed', help='Seed IP address for initial discovery')
        parser.add_argument('--community', default='public')
        parser.add_argument(
            '--async', action='store_true', dest='async',
            help='Run the scan asynchronously via Celery'
        )

    def handle(self, *args, **options):
        community = options['community']
        seed_ip = options.get('seed')
        use_async = options.get('async')

        if seed_ip:
            if use_async:
                from inventory.tasks import discover_network_task
                result = discover_network_task.delay(seed_ip, community)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Started async discover_network task {result.id}'
                    )
                )
            else:
                visited = discover_network(seed_ip, community)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Discovered {len(visited)} devices'
                    )
                )
        else:
            if use_async:
                from inventory.tasks import periodic_scan_task
                result = periodic_scan_task.delay(community)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Started async periodic_scan task {result.id}'
                    )
                )
            else:
                scanned = periodic_scan(community)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Scanned {len(scanned)} devices'
                    )
                )
