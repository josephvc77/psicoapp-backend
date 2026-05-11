#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Usando versión de Python: $(python --version)"

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate
