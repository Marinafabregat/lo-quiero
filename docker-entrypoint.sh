#!/bin/sh
set -e

echo "Aplicando migraciones pendientes…"
python manage.py migrate --noinput

echo "Iniciando «¿Lo quiero?»…"
exec "$@"
