# Solución al Error HTTPS/HTTP

## Problema
Si recibes el error:
```
You're accessing the development server over HTTPS, but it only supports HTTP.
code 400, message Bad request version
```

## Solución

### 1. Verificar que el servidor Django esté corriendo correctamente

Asegúrate de iniciar el servidor con `0.0.0.0` para aceptar conexiones desde la red local:

```bash
cd PsicoAppBackend
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

**IMPORTANTE:** Usa `0.0.0.0:8000` en lugar de solo `localhost:8000` o `127.0.0.1:8000`

### 2. Verificar tu IP local

Ejecuta uno de estos comandos para obtener tu IP local:

**En Mac/Linux:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

**En Windows:**
```bash
ipconfig
```

Busca la IP en la sección de tu conexión WiFi o Ethernet (ej: `192.168.31.119`)

### 3. Actualizar la configuración del frontend

Asegúrate de que en `PsicoApp/config/api.ts` esté configurada tu IP local:

```typescript
const MANUAL_IP = 'TU_IP_LOCAL'; // Ejemplo: '192.168.31.119'
```

### 4. Verificar que estés usando HTTP (no HTTPS)

La URL debe ser:
- ✅ `http://192.168.31.119:8000/api` (correcto)
- ❌ `https://192.168.31.119:8000/api` (incorrecto)

### 5. Si usas Expo Go

1. Asegúrate de que tu móvil y tu computadora estén en la misma red WiFi
2. Verifica que el firewall no esté bloqueando el puerto 8000
3. Intenta reiniciar el servidor Django

### 6. Verificar la configuración de Django

En `psicoapp_backend/settings.py`:
- `ALLOWED_HOSTS` debe incluir tu IP local
- `CORS_ALLOW_ALL_ORIGINS = True` en desarrollo
- El servidor debe estar corriendo con `0.0.0.0:8000`

### 7. Probar la conexión

Abre en tu navegador (desde tu computadora):
```
http://TU_IP_LOCAL:8000/api/
```

Deberías ver la página de la API de Django REST Framework. Si funciona desde el navegador pero no desde el móvil, el problema es de red/firewall.

### 8. Si el problema persiste

1. **Reinicia el servidor Django:**
   ```bash
   # Detener el servidor (Ctrl+C)
   # Luego iniciarlo de nuevo:
   python manage.py runserver 0.0.0.0:8000
   ```

2. **Verifica el firewall:**
   - En Mac: Preferencias del Sistema > Seguridad y Privacidad > Firewall
   - Asegúrate de que Python tenga permisos de red

3. **Prueba desde el navegador del móvil:**
   - Abre `http://TU_IP_LOCAL:8000/api/` en el navegador de tu móvil
   - Si no carga, el problema es de red/firewall

4. **Revisa los logs del servidor Django:**
   - Deberías ver las peticiones entrantes en la terminal donde corre el servidor
   - Si no ves ninguna petición, el problema es de red

