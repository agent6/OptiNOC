# OptiNOC Backlog

This file collects potential enhancements inspired by features from [LibreNMS](https://github.com/librenms/librenms) that could be implemented in OptiNOC.

## Discovery Enhancements
- **Auto-Discovery Modules**: Support ARP, CDP/LLDP, OSPF, OSPFv3 and BGP based discovery as configurable modules similar to LibreNMS.
- **SNMP Scan Utility**: Provide a script or management command to proactively scan subnets for SNMP-enabled devices, with options like thread count and ping-only mode.
- **Discovery Exclusions**: Allow networks, devices, or platforms to be excluded from automated discovery.

## Application Monitoring
- **SNMP Extend / Agent**: Implement an application monitoring framework that can collect metrics via SNMP extend scripts or a lightweight agent.
- **Return Optimizer**: Consider adopting a compressed JSON return method for large SNMP extend outputs as described in LibreNMS documentation.
- **Application Library**: Provide built-in support for common applications (e.g., Redis, Docker, UPS) that users can enable per device.

## Configuration Management
- **Oxidized Integration**: Integrate with Oxidized for configuration backup, version history, and diff viewing within the device page.
- **Grouping & Overrides**: Allow mapping of device attributes (hostname, OS, location) to Oxidized groups and support custom per-device parameters.
- **Trigger Backups**: Offer hooks or scripts so configuration downloads can be triggered from syslog events.

## Performance & Scaling
- **RRDCached Support**: Add optional support for RRDCached to improve RRD write performance and enable distributed poller setups.
- **Distributed Pollers**: Plan for multiple polling workers with shared storage or centralized metrics.

## Alerting & API
- **Alert Rules and Templates**: Expand the alerting system with rule-based conditions, customizable templates, and multiple transport options (email, webhook, etc.).
- **REST API**: Provide documented API endpoints for managing devices, fetching metrics, and exporting configuration data.

## Deployment & Tools
- **Docker Image**: Offer an official Docker image for quick deployment, similar to LibreNMS.
- **Install Validation Tool**: Include a command to validate installation and environment similar to LibreNMS `validate.php`.

