# OptiNOC

**OptiNOC** is an open-source, intelligent network discovery and monitoring platform built with Django. Designed as a modern alternative to traditional tools like Auvik, OptiNOC provides comprehensive network visibility, asset fingerprinting, real-time monitoring, and logical topology mapping.

**Important:** Perform network discovery and scanning only on networks where you have explicit permission. Misuse could violate laws or organizational policies.

---

**⚠️ Responsible Use:** Perform discovery and scanning only on networks where you have explicit permission. Misuse may violate laws or organizational policies.

## 🚀 Features

- **Automated Network Discovery**  
  Uses SNMP, SSH, Telnet, CDP, LLDP, ARP/CAM tables, HTTP(S), and more to identify assets and map connections.

- **Asset Fingerprinting & Inventory**  
  Classifies devices with vendor, model, OS, interface data, and environmental metadata.

- **Logical Network Mapping**  
  Visualizes device relationships and topologies based on link-layer discovery and MAC/IP mapping.

- **Roadblock Identification**  
  Highlights missing credentials, incorrect SNMP community strings, blocked ports, and other issues that prevent full visibility.

- **Monitoring & Baselines**  
  Tracks device performance (CPU, memory, interface stats), uptime, and latency over time with graphs and alerting.

- **Tags, Alerts & Profiles**  
  Organize assets with tags and configure threshold-based alert profiles to fit your environment.

- **On-Premise & Secure**  
  Built for single-organization use with Django local auth and on-premise deployment. No cloud dependencies.

---

## 📸 Screenshots

*(Coming soon — UI views of asset tables, graphs, and the topology map.)*

---

## 📦 Tech Stack

- **Backend:** Django, Celery, PostgreSQL/SQLite  
- **Frontend:** Django Templates, Bootstrap 5, Chart.js, JS topology lib (e.g. D3.js or Cytoscape)  
- **Network Discovery:** pysnmp, Netmiko, custom parsers  
- **Task Queue:** Celery with Redis  
- **Architecture:** Modular, scalable, async-capable

---

## ⚙️ Installation (Development)

```bash
git clone https://github.com/yourusername/OptiNOC.git
cd OptiNOC
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set up environment variables (or use .env file)
export DJANGO_SECRET_KEY='your-secret-key'
export DB_NAME='optinoc_db'
export CELERY_BROKER_URL='redis://localhost:6379/0'

# Optional static and media locations
export STATIC_ROOT="$PWD/static_root"
export MEDIA_ROOT="$PWD/media"

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start the server
python manage.py runserver

# Start Celery worker
celery -A optinoc worker -l info
```

### Static & Media Files

Run `python manage.py collectstatic` to copy Bootstrap and other assets into `STATIC_ROOT`. User uploads will be stored in `MEDIA_ROOT`.

For network scanning:

* Ensure `snmpwalk`, Redis, and necessary ports are available.
* Celery for async scans.

---

## License
This project is released under the MIT License. See [LICENSE](LICENSE) for details.


