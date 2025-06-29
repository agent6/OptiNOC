#!/usr/bin/env bash
set -euo pipefail

# Simple deployment script for on‑premise installation of OptiNOC
# ───────────────────────────────────────────────────────────────
# Optional environment variables (override defaults for automation):
#   REPO_URL            – Git repository to clone from
#   APP_DIR             – Absolute install directory (must be writable)
#   PYTHON              – Python executable to use for venv
#   DJANGO_SECRET_KEY   – Service environment; falls back to "changeme"
#   ALLOWED_HOSTS       – Comma‑separated list consumed by Django
#   SUPERUSER_USERNAME  – Seed these three to create the first admin
#   SUPERUSER_EMAIL     –   account non‑interactively during install
#   SUPERUSER_PASSWORD  –
#
#   If any of the three SUPERUSER_* variables is missing the script will
#   fall back to an interactive prompt (unless STDIN is non‑TTY, in which
#   case the super‑user step is skipped with a warning).

REPO_URL=${REPO_URL:-https://github.com/agent6/OptiNOC.git}
APP_DIR=${APP_DIR:-/opt/optinoc}
PYTHON=${PYTHON:-python3}

sudo apt-get update
sudo apt-get install -y git python3-venv python3-dev build-essential redis-server \
    graphviz graphviz-dev libgraphviz-dev pkg-config

# ────────────────────────────── Clone or update repo ─────────────────────────────
if [ ! -d "$APP_DIR" ]; then
    sudo mkdir -p "$APP_DIR"
    sudo chown $(whoami):$(whoami) "$APP_DIR"
    git clone "$REPO_URL" "$APP_DIR"
else
    git -C "$APP_DIR" pull --ff-only
fi

cd "$APP_DIR"

# ───────────────────────────── Python virtual‑env ────────────────────────────────
if [ ! -d "venv" ]; then
    $PYTHON -m venv venv
fi
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

# ──────────────────────────────── Django setup ───────────────────────────────────
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# ─────────────────────── Create initial Django super‑user ───────────────────────
create_superuser() {
    local u="$1" e="$2" p="$3"
    echo "• Creating Django super‑user '$u' …"
    DJANGO_SUPERUSER_PASSWORD="$p" python manage.py createsuperuser \
        --noinput --username "$u" --email "$e" || true
}

if [[ -n "${SUPERUSER_USERNAME:-}" && -n "${SUPERUSER_EMAIL:-}" && -n "${SUPERUSER_PASSWORD:-}" ]]; then
    # Non‑interactive path (CI/CD friendly)
    create_superuser "$SUPERUSER_USERNAME" "$SUPERUSER_EMAIL" "$SUPERUSER_PASSWORD"
else
    if [ -t 0 ]; then
        read -rp "Create Django super‑user now? [y/N]: " ans
        if [[ "$ans" =~ ^[Yy]$ ]]; then
            read -rp "Username: " su_user
            read -rp "Email   : " su_email
            while true; do
                read -srp "Password: " su_pass && echo
                read -srp "Confirm : " su_pass2 && echo
                [[ "$su_pass" == "$su_pass2" ]] && break
                echo "Passwords do not match; try again." >&2
            done
            create_superuser "$su_user" "$su_email" "$su_pass"
        else
            echo "Skipping super‑user creation. You can run 'python manage.py createsuperuser' later." >&2
        fi
    else
        echo "STDIN is not a TTY; skipping super‑user creation. Set SUPERUSER_* vars or run manually later." >&2
    fi
fi

# ─────────────────────────── systemd service unit ───────────────────────────────
SERVICE_FILE=/etc/systemd/system/optinoc.service
sudo tee "$SERVICE_FILE" >/dev/null <<SERVICE
[Unit]
Description=OptiNOC Gunicorn Service
After=network.target

[Service]
Type=simple
User=$(whoami)
Group=$(whoami)
WorkingDirectory=$APP_DIR
Environment=DJANGO_SECRET_KEY=\${DJANGO_SECRET_KEY:-changeme}
Environment=ALLOWED_HOSTS=\${ALLOWED_HOSTS:-*}
ExecStart=$APP_DIR/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:8000 optinoc.wsgi:application

[Install]
WantedBy=multi-user.target
SERVICE

sudo systemctl daemon-reload
sudo systemctl enable --now optinoc.service

echo "\n✅ OptiNOC deployed and running via systemd service 'optinoc'."
if systemctl is-active --quiet optinoc.service; then
    echo "   Access the app at http://<server>:8000/ and /admin/ with the super‑user you just created."
fi
