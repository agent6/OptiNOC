# OptiNOC

**OptiNOC** is an open-source, intelligent network discovery and monitoring platform built with Django. Designed as a modern alternative to traditional tools like Auvik, OptiNOC provides comprehensive network visibility, asset fingerprinting, real-time monitoring, and logical topology mapping.

The project is mirrored on GitHub at [agent6/OptiNOC](https://github.com/agent6/OptiNOC).

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
  Tracks device performance (CPU, memory, interface stats), uptime, and latency over time with graphs and alerting. Includes periodic ICMP ping checks for availability monitoring.
- **Historical Metrics Storage**
  Metric data points are stored in the `MetricRecord` table with indexed timestamps so charts can efficiently query a date range.
- **Interactive Graphs**
  Device and interface detail pages display historical CPU and bandwidth graphs rendered with Chart.js and HTMX powered AJAX requests.

- **Tags, Alerts & Profiles**
  Organize assets with tags and configure threshold-based alert profiles to fit your environment.

**Automated Alert Evaluation**
  Metrics collected during polling are compared to alert profiles each cycle and alerts are created or cleared automatically.

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
git clone https://github.com/agent6/OptiNOC.git
cd OptiNOC
# For Ubuntu/Debian you can run the helper script
./scripts/setup_ubuntu.sh

python -m venv venv
source venv/bin/activate
# Ubuntu: install Graphviz libraries for pygraphviz
sudo apt-get install -y graphviz graphviz-dev libgraphviz-dev pkg-config

pip install -r requirements.txt

# Set up environment variables (or use .env file)
export DJANGO_SECRET_KEY='your-secret-key'
export DB_NAME='optinoc_db'
export CELERY_BROKER_URL='redis://localhost:6379/0'

# Optional: use PostgreSQL instead of SQLite
export USE_POSTGRES=true
export DB_USER='optinoc'
export DB_PASSWORD='secret'
export DB_HOST='localhost'
export DB_PORT='5432'

# Celery result backend (defaults to broker URL)
export CELERY_RESULT_BACKEND='redis://localhost:6379/0'

# Optional static and media locations
export STATIC_ROOT="$PWD/static_root"
export MEDIA_ROOT="$PWD/media"

# Run migrations
python manage.py migrate

# Create superuser
scripts/create_superuser.sh

# Access the Django administration site at http://localhost:8000/admin and
# manage devices, interfaces, tags and alert profiles using the account created
# above.

# Start the server
python manage.py runserver

# Start Celery worker
celery -A optinoc worker -l info
# Start Celery beat scheduler
celery -A optinoc beat -l info
```
### Environment Variables

- **DJANGO_SECRET_KEY** – secret key for Django
- **USE_POSTGRES** – set to `true` to enable PostgreSQL settings
- **DB_NAME**, **DB_USER**, **DB_PASSWORD**, **DB_HOST**, **DB_PORT** – PostgreSQL connection details
- **CELERY_BROKER_URL** – URL of the Celery broker (e.g. Redis)
- **CELERY_RESULT_BACKEND** – where Celery stores task results
- **STATIC_ROOT** / **MEDIA_ROOT** – paths for collected static files and media
- **ALLOWED_HOSTS** – comma separated hosts allowed when running in production


### Static & Media Files

Run `python manage.py collectstatic` to copy Bootstrap and other assets into `STATIC_ROOT`. User uploads will be stored in `MEDIA_ROOT`.

## Usage

After starting the server and Celery workers, log in to the Django admin at http://localhost:8000/admin.
Add devices with management IP addresses and provide SNMP communities or SSH credentials.

For network scanning:

* Ensure `snmpwalk` and Redis are installed and accessible.
* Run `python manage.py scan_network --seed <IP>` for an initial discovery scan. Add `--async` to offload to Celery.
* Periodic scans and metric polling will run automatically when Celery beat is active.

Each device has a **roadblocks** field listing issues encountered during discovery, such as unreachable hosts or invalid credentials. Resolve these to improve network visibility.

## 🏭 On-Premise Deployment

For a one-step install on a fresh Ubuntu server, run:

```bash
curl -L https://raw.githubusercontent.com/agent6/OptiNOC/main/scripts/install_onprem.sh | bash
```

The script clones this repository, installs system and Python dependencies, runs migrations and collects static files, then starts Gunicorn via a systemd service so OptiNOC launches automatically after reboot.



---

## License
This project is released under the MIT License. See [LICENSE](LICENSE) for details.


