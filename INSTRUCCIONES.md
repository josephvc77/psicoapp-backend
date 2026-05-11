# Instrucciones para ejecutar el Backend

## Requisitos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)

## Pasos para iniciar el servidor

1. **Navegar a la carpeta del backend:**
```bash
cd PsicoAppBackend
```

2. **Activar el entorno virtual:**
```bash
# En macOS/Linux:
source venv/bin/activate

# En Windows:
venv\Scripts\activate
```

3. **Instalar dependencias (si no están instaladas):**
```bash
pip install -r requirements.txt
```

4. **Ejecutar migraciones (si es la primera vez):**
```bash
python manage.py migrate
```

5. **Crear superusuario (OBLIGATORIO para acceder al admin):**
```bash
python manage.py createsuperuser
```
   - Te pedirá: Email, Username, Password
   - Este usuario tendrá acceso completo al panel de administración

6. **Iniciar el servidor:**
```bash
# Para desarrollo web (solo localhost):
python manage.py runserver

# Para desarrollo móvil (Expo Go) - IMPORTANTE usar 0.0.0.0:
python manage.py runserver 0.0.0.0:8000
```

El servidor estará disponible en: **http://localhost:8000**

**Nota para desarrollo móvil:** Si vas a usar Expo Go, DEBES usar `0.0.0.0:8000` para que el servidor escuche en todas las interfaces de red y sea accesible desde tu móvil.

## Acceder al panel de administración

1. Abre tu navegador en: `http://localhost:8000/admin`
2. Inicia sesión con las credenciales del superusuario que creaste

### Funcionalidades del Panel de Administración

El panel de administración está completamente configurado con:

#### **Gestión de Usuarios**
- Ver todos los usuarios registrados
- Filtrar por staff, superusuario, fecha de registro
- Buscar por email o username
- Enlaces directos a los perfiles de usuario

#### **Perfiles de Usuario**
- Ver información física (altura, peso, edad, género)
- Ver porcentaje de grasa corporal
- Estado de onboarding
- Enlaces directos al usuario

#### **Planes de Alimentación**
- Ver todos los planes (públicos y personalizados)
- Filtrar por categoría, dificultad, tipo (custom/público)
- Ver planes creados por IA
- Buscar por título o descripción

#### **Seguimiento Nutricional**
- Ver todas las entradas de seguimiento
- Ver comidas completadas con porcentaje visual
- Filtrar por fecha y plan
- Navegación jerárquica por fecha

#### **Rutinas de Ejercicio**
- Ver todas las rutinas (públicas y personalizadas)
- Ver número de ejercicios en cada rutina
- Filtrar por categoría, dificultad, días por semana
- Buscar por título o descripción

#### **Seguimiento de Ejercicio**
- Ver todas las sesiones de ejercicio
- Ver porcentaje de ejercicios completados
- Filtrar por fecha y rutina
- Ver duración de cada sesión

#### **Seguimiento de Ánimo**
- Ver todas las entradas de ánimo
- Visualización con colores (rojo=muy malo, verde=muy bueno)
- Filtrar por nivel de ánimo y fecha
- Ver si tiene notas

#### **Sesiones de IA (Psicología)**
- Ver todas las sesiones con psicólogo IA
- Ver ánimo antes y después de la sesión
- Ver duración de cada sesión
- Ver resumen de conversación

#### **Hidratación**
- Ver todas las entradas de hidratación
- Ver progreso visual con porcentaje (verde=nivel alcanzado, rojo=por debajo)
- Filtrar por fecha
- Ver cantidad vs meta diaria

### Características del Admin

✅ **Enlaces cruzados**: Navega fácilmente entre usuarios, perfiles, planes y entradas
✅ **Filtros avanzados**: Filtra por múltiples criterios simultáneamente
✅ **Búsqueda**: Busca en todos los campos relevantes
✅ **Visualización mejorada**: Colores y porcentajes para mejor comprensión
✅ **Navegación por fecha**: Jerarquía de fechas para encontrar entradas rápidamente
✅ **Información contextual**: Muestra relaciones entre modelos (usuario → perfil → entradas)

## Notas importantes

- El backend usa SQLite por defecto (archivo `db.sqlite3`)
- Para desarrollo, CORS está configurado para permitir todas las conexiones
- En producción, debes cambiar `CORS_ALLOW_ALL_ORIGINS = False` y configurar `CORS_ALLOWED_ORIGINS`
- La URL base de la API es: `http://localhost:8000/api`

## Solución de problemas

### Error: "No module named 'django'"
- Asegúrate de haber activado el entorno virtual
- Ejecuta: `pip install -r requirements.txt`

### Error: "Port 8000 already in use"
- Cambia el puerto: `python manage.py runserver 8001`
- Actualiza la URL en `PsicoApp/services/apiService.ts`

### Error de CORS
- Verifica que `CORS_ALLOW_ALL_ORIGINS = True` en `settings.py` (solo para desarrollo)
- Verifica que la URL en `apiService.ts` coincida con la del servidor

