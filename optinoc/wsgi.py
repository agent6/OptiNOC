import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'optinoc.settings')

application = get_wsgi_application()

# Trigger an initial inventory scan when the server starts
try:
    from inventory.discovery import periodic_scan
    periodic_scan()
except Exception:
    # Ignore any issues so startup is never blocked
    pass
