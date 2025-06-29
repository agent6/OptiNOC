#!/usr/bin/env bash
set -euo pipefail

if [ ! -f "venv/bin/activate" ]; then
    echo "Virtual environment not found. Run scripts/setup_ubuntu.sh first." >&2
    exit 1
fi
source venv/bin/activate

read -p "Enter superuser username: " USERNAME
read -p "Enter email address: " EMAIL
read -s -p "Enter password: " PASSWORD
echo
read -s -p "Confirm password: " PASSWORD_CONFIRM
echo
if [ "$PASSWORD" != "$PASSWORD_CONFIRM" ]; then
    echo "Passwords do not match." >&2
    exit 1
fi

# optional: very light e-mail sanity check
if [[ ! "$EMAIL" =~ .+@.+\..+ ]]; then
    echo "That doesn't look like a valid e-mail address." >&2
    exit 1
fi

DJANGO_SUPERUSER_PASSWORD="$PASSWORD" \
python manage.py createsuperuser --noinput \
    --username "$USERNAME" \
    --email    "$EMAIL"

echo "Superuser '$USERNAME' created."
