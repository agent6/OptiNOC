#!/usr/bin/env bash
set -euo pipefail

# Simple deployment script for on-premise installation

REPO_URL=${REPO_URL:-https://github.com/agent6/OptiNOC.git}
APP_DIR=${APP_DIR:-/opt/optinoc}
PYTHON=${PYTHON:-python3}

sudo apt-get update
sudo apt-get install -y git python3-venv python3-dev build-essential redis-server \
    graphviz graphviz-dev libgraphviz-dev pkg-config

# clone or update repo
if [ ! -d "$APP_DIR" ]; then
    sudo mkdir -p "$APP_DIR"
    sudo chown $(whoami):$(whoami) "$APP_DIR"
    git clone "$REPO_URL" "$APP_DIR"
else
    git -C "$APP_DIR" pull
fi

cd "$APP_DIR"

if [ ! -d "venv" ]; then
    $PYTHON -m venv venv
fi
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

python manage.py migrate --noinput
python manage.py collectstatic --noinput

sudo tee /etc/systemd/system/optinoc.service > /dev/null <<SERVICE
[Unit]
Description=OptiNOC Gunicorn Service
After=network.target

[Service]
Type=simple
User=$(whoami)
Group=$(whoami)
WorkingDirectory=$APP_DIR
Environment=DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY:-changeme}
Environment=ALLOWED_HOSTS=${ALLOWED_HOSTS:-*}
ExecStart=$APP_DIR/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:8000 optinoc.wsgi:application

[Install]
WantedBy=multi-user.target
SERVICE

sudo systemctl daemon-reload
sudo systemctl enable --now optinoc.service

echo "OptiNOC deployed and running via systemd service 'optinoc'."
