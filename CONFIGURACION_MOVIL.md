# 📱 Configuración para Desarrollo Móvil (Expo Go)

Esta guía te ayudará a configurar el backend para que funcione con Expo Go en tu dispositivo móvil.

## 🔧 Pasos de Configuración

### 1. Obtener tu IP Local

**En Mac/Linux:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

**En Windows:**
```cmd
ipconfig
```

Busca la IP en la sección de tu conexión WiFi o Ethernet (ej: `192.168.1.100`)

### 2. Configurar el Backend para Escuchar en Todas las Interfaces

El backend ya está configurado para escuchar en `0.0.0.0:8000`, lo que permite conexiones desde cualquier dispositivo en tu red local.

### 3. Configurar la IP en el Frontend

1. Abre el archivo: `PsicoApp/config/api.ts`
2. Busca la línea: `const MANUAL_IP = 'TU_IP_LOCAL';`
3. Reemplaza `'TU_IP_LOCAL'` con tu IP local (ej: `'192.168.1.100'`)
4. Guarda el archivo

**Ejemplo:**
```typescript
const MANUAL_IP = '192.168.1.100'; // Tu IP local
```

### 4. Iniciar el Backend

```bash
cd PsicoAppBackend
source venv/bin/activate  # En Windows: venv\Scripts\activate
python manage.py runserver 0.0.0.0:8000
```

**Importante:** Usa `0.0.0.0:8000` en lugar de solo `8000` para que escuche en todas las interfaces de red.

### 5. Verificar que el Backend Esté Accesible

Abre en tu navegador (desde tu computadora):
- `http://localhost:8000/admin/` - Debe funcionar
- `http://TU_IP_LOCAL:8000/admin/` - También debe funcionar (reemplaza TU_IP_LOCAL)

### 6. Iniciar Expo

```bash
cd PsicoApp
npx expo start
```

Luego escanea el código QR con Expo Go en tu móvil.

### 7. Verificar la Conexión

Cuando inicies sesión desde tu móvil, deberías poder conectarte al backend. Si hay problemas:

1. **Verifica el firewall:** Asegúrate de que el puerto 8000 esté abierto
2. **Verifica la IP:** Confirma que la IP en `config/api.ts` sea correcta
3. **Verifica la red:** Asegúrate de que tu móvil y computadora estén en la misma red WiFi

## 🔍 Solución de Problemas

### Error: "Network request failed"
- Verifica que el backend esté corriendo en `0.0.0.0:8000`
- Verifica que la IP en `config/api.ts` sea correcta
- Verifica que ambos dispositivos estén en la misma red WiFi

### Error: "Connection refused"
- Verifica que el firewall no esté bloqueando el puerto 8000
- En Mac, ve a: Sistema > Seguridad > Firewall > Opciones
- Permite conexiones entrantes para Python

### Error de CORS
- El backend ya está configurado con `CORS_ALLOW_ALL_ORIGINS = True` para desarrollo
- Si persiste, verifica `settings.py` línea 155

## 📝 Notas

- La IP local puede cambiar si te conectas a una red diferente
- En producción, usa una URL de dominio real
- Para desarrollo, considera usar `ngrok` o similar para pruebas remotas

