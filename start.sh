#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Ejecutando migraciones..."
python manage.py migrate

echo "Arrancando servidor..."
daphne -b 0.0.0.0 -p 8000 psicoapp_backend.asgi:application
