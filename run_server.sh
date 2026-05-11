#!/bin/bash

# Script para ejecutar el servidor Django con soporte para WebSockets
# Usa daphne (ASGI) en lugar de runserver para soportar WebSockets

echo "🚀 Iniciando servidor Django con soporte para WebSockets..."
echo "📡 WebSocket disponible en: ws://localhost:8000/ws/notifications/"
echo ""

# Ejecutar con daphne
daphne psicoapp_backend.asgi:application --bind 0.0.0.0 --port 8000

