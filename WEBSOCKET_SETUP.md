# Configuración de WebSockets para Notificaciones en Tiempo Real

## Instalación

1. Instalar Django Channels:
```bash
pip install channels>=4.0.0
```

O instalar todas las dependencias:
```bash
pip install -r requirements.txt
```

## Ejecutar el servidor

Para que los WebSockets funcionen, necesitas ejecutar el servidor con ASGI en lugar de WSGI:

```bash
# En lugar de: python manage.py runserver
# Usa:
daphne psicoapp_backend.asgi:application

# O con uvicorn (si lo prefieres):
uvicorn psicoapp_backend.asgi:application --host 0.0.0.0 --port 8000
```

### Instalar daphne o uvicorn:

```bash
pip install daphne
# O
pip install uvicorn
```

## Verificar que funciona

1. El servidor debería mostrar mensajes como:
   - `[WebSocket] Usuario X conectado a notificaciones`
   - `[WebSocket] Notificación enviada a usuario X`

2. En el frontend, deberías ver en la consola:
   - `[WebSocket] Connected`
   - `[WebSocket] Message received: notification`

## Notas

- El WebSocket se conecta automáticamente cuando el usuario está autenticado
- Si el WebSocket falla, el sistema usa polling como fallback (cada 10 segundos)
- La conexión se reconecta automáticamente si se pierde

