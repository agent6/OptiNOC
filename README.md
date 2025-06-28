# OptiNOC

**OptiNOC** is an open-source, intelligent network discovery and monitoring platform built with Django. Designed as a modern alternative to traditional tools like Auvik, OptiNOC provides comprehensive network visibility, asset fingerprinting, real-time monitoring, and logical topology mapping.

---

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

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start the server
python manage.py runserver
````

For network scanning:

* Ensure `snmpwalk`, Redis, and necessary ports are available.
* Celery for async scans.

---

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT). See the [LICENSE](LICENSE) file for details.

