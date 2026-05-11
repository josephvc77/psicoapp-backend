# 🔧 Implementación de Mejoras de Seguridad

Este documento contiene los cambios específicos que debes implementar para mejorar la seguridad de tu aplicación.

## 1. Configurar Variables de Entorno

### Paso 1: Instalar python-decouple
```bash
cd PsicoAppBackend
pip install python-decouple
```

### Paso 2: Crear archivo `.env`
Crea un archivo `.env` en `PsicoAppBackend/`:
```env
SECRET_KEY=tu-secret-key-super-segura-aqui-genera-una-nueva
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,tu-dominio.com
CORS_ALLOWED_ORIGINS=http://localhost:8081,https://tu-dominio.com
```

### Paso 3: Actualizar `settings.py`
```python
from decouple import config
import os

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-fallback-key-only-for-dev')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

# CORS configuration
CORS_ALLOW_ALL_ORIGINS = config('CORS_ALLOW_ALL_ORIGINS', default=False, cast=bool)
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='').split(',')
```

### Paso 4: Agregar `.env` a `.gitignore`
```gitignore
.env
*.pyc
__pycache__/
db.sqlite3
```

## 2. Implementar Rate Limiting

### Paso 1: Instalar django-ratelimit
```bash
pip install django-ratelimit
```

### Paso 2: Agregar a `INSTALLED_APPS`
```python
INSTALLED_APPS = [
    # ... otros apps
    'django_ratelimit',
]
```

### Paso 3: Actualizar `api/views.py`
```python
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

class AuthViewSet(viewsets.ViewSet):
    """ViewSet para autenticación"""
    permission_classes = [AllowAny]

    @method_decorator(ratelimit(key='ip', rate='5/m', method='POST'))
    @action(detail=False, methods=['post'])
    def register(self, request):
        """Registro de nuevo usuario"""
        # ... código existente

    @method_decorator(ratelimit(key='ip', rate='5/m', method='POST'))
    @action(detail=False, methods=['post'])
    def login(self, request):
        """Inicio de sesión"""
        # ... código existente

    @method_decorator(ratelimit(key='ip', rate='10/m', method='POST'))
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def check_email(self, request):
        """Verificar si un email ya está registrado"""
        # ... código existente

    @method_decorator(ratelimit(key='ip', rate='10/m', method='POST'))
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def check_username(self, request):
        """Verificar si un username ya está en uso"""
        # ... código existente
```

## 3. Agregar Validación de Tamaño de Avatar

### Actualizar `api/serializers.py`
```python
class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer para el perfil de usuario"""
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'height', 'weight', 'age', 'gender',
            'body_fat_percentage', 'avatar_url', 'has_completed_onboarding',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_avatar_url(self, value):
        """Validar tamaño de avatar (máximo 5MB en base64)"""
        if value and value.startswith('data:image'):
            # Base64 es aproximadamente 33% más grande que el archivo original
            # 5MB = 5 * 1024 * 1024 bytes
            size_bytes = len(value.encode('utf-8'))
            max_size_bytes = 5 * 1024 * 1024  # 5MB
            
            if size_bytes > max_size_bytes:
                raise serializers.ValidationError(
                    f"La imagen es demasiado grande. Tamaño máximo: 5MB. "
                    f"Tamaño actual: {(size_bytes / (1024 * 1024)).toFixed(2)}MB"
                )
        return value
```

## 4. Agregar Headers de Seguridad

### Actualizar `settings.py`
```python
# Security Headers
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000  # 1 año
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
```

## 5. Mejorar Validación de Email en Frontend

### Actualizar `PsicoApp/app/signup.tsx`
```typescript
const EMAIL_REGEX = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;

// En la función de validación
if (!EMAIL_REGEX.test(email)) {
  return { success: false, error: 'Correo electrónico inválido' };
}
```

## 6. Agregar Timeout a Requests

### Actualizar `PsicoApp/services/apiService.ts`
```typescript
async request<T>(
  endpoint: string,
  options: RequestInit = {},
  timeout: number = 10000  // 10 segundos por defecto
): Promise<ApiResponse<T>> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      headers['Authorization'] = `Token ${this.token}`;
    }

    const fullUrl = `${API_BASE_URL}${endpoint}`;
    
    if (__DEV__) {
      console.log('🌐 API Request:', {
        method: options.method || 'GET',
        url: fullUrl,
        hasToken: !!this.token,
      });
    }

    const response = await fetch(fullUrl, {
      ...options,
      headers,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    // ... resto del código
  } catch (error: any) {
    if (error.name === 'AbortError') {
      return {
        success: false,
        error: 'La petición tardó demasiado. Por favor, intenta de nuevo.',
      };
    }
    return {
      success: false,
      error: error.message || 'Error de conexión',
    };
  }
}
```

## 7. Validar Tamaño de Imagen en Frontend

### Actualizar `PsicoApp/app/cambiar-avatar.tsx`
```typescript
const MAX_IMAGE_SIZE = 5 * 1024 * 1024; // 5MB

const convertImageToBase64 = async (uri: string): Promise<string> => {
  try {
    // Verificar tamaño del archivo
    const fileInfo = await FileSystem.getInfoAsync(uri);
    if (fileInfo.exists && fileInfo.size && fileInfo.size > MAX_IMAGE_SIZE) {
      throw new Error(`La imagen es demasiado grande. Tamaño máximo: 5MB. Tamaño actual: ${(fileInfo.size / (1024 * 1024)).toFixed(2)}MB`);
    }

    // ... resto del código de conversión
  } catch (error) {
    console.error('Error converting image to base64:', error);
    throw error;
  }
};
```

## 8. Actualizar requirements.txt

```txt
Django==4.2.7
djangorestframework==3.14.0
django-cors-headers==4.3.1
python-decouple==3.8
django-jazzmin==2.6.0
django-ratelimit==4.0.0
```

## 9. Generar Nueva SECRET_KEY

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copia el resultado y úsalo en tu archivo `.env`.

## 10. Verificar Cambios

Después de implementar estos cambios:

1. **Probar en desarrollo:**
   ```bash
   python manage.py runserver
   ```

2. **Verificar que el .env no esté en git:**
   ```bash
   git status
   ```

3. **Probar rate limiting:**
   - Intentar hacer más de 5 login attempts en un minuto
   - Debería recibir un error 429 (Too Many Requests)

4. **Probar validación de avatar:**
   - Intentar subir una imagen mayor a 5MB
   - Debería recibir un error de validación

---

**Nota:** Estos cambios mejoran significativamente la seguridad, pero siempre hay más que se puede hacer. Revisa regularmente las actualizaciones de seguridad de Django y las dependencias.

