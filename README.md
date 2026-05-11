# PsicoApp Backend

Backend Django REST Framework para la aplicación PsicoApp.

## Instalación

1. Crear y activar el entorno virtual:
```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Ejecutar migraciones:
```bash
python manage.py migrate
```

4. Crear superusuario (opcional):
```bash
python manage.py createsuperuser
```

5. Iniciar el servidor:
```bash
python manage.py runserver
```

El servidor estará disponible en `http://localhost:8000`

## Endpoints API

### Autenticación
- `POST /api/auth/register/` - Registro de usuario
- `POST /api/auth/login/` - Inicio de sesión
- `POST /api/auth/logout/` - Cerrar sesión

### Usuarios
- `GET /api/users/me/` - Obtener usuario actual

### Perfiles
- `GET /api/profiles/me/` - Obtener perfil actual
- `PUT /api/profiles/me/` - Actualizar perfil

### Planes de Alimentación
- `GET /api/meal-plans/` - Listar planes
- `POST /api/meal-plans/` - Crear plan
- `GET /api/meal-plans/custom/` - Obtener planes personalizados

### Seguimiento Nutricional
- `GET /api/nutrition-entries/` - Listar entradas
- `POST /api/nutrition-entries/` - Crear entrada
- `GET /api/nutrition-entries/by_date/?date=YYYY-MM-DD` - Obtener por fecha

### Rutinas de Ejercicio
- `GET /api/exercise-routines/` - Listar rutinas
- `POST /api/exercise-routines/` - Crear rutina
- `GET /api/exercise-routines/custom/` - Obtener rutinas personalizadas

### Seguimiento de Ejercicio
- `GET /api/exercise-entries/` - Listar entradas
- `POST /api/exercise-entries/` - Crear entrada
- `GET /api/exercise-entries/by_date/?date=YYYY-MM-DD` - Obtener por fecha
- `GET /api/exercise-entries/weekly_stats/` - Estadísticas semanales

### Seguimiento de Ánimo
- `GET /api/mood-entries/` - Listar entradas
- `POST /api/mood-entries/` - Crear entrada
- `GET /api/mood-entries/by_date/?date=YYYY-MM-DD` - Obtener por fecha

### Sesiones de IA
- `GET /api/ai-sessions/` - Listar sesiones
- `POST /api/ai-sessions/` - Crear sesión
- `GET /api/ai-sessions/by_date/?date=YYYY-MM-DD` - Obtener por fecha

### Hidratación
- `GET /api/hydration-entries/` - Listar entradas
- `POST /api/hydration-entries/` - Crear entrada
- `GET /api/hydration-entries/by_date/?date=YYYY-MM-DD` - Obtener por fecha

## Autenticación

Todas las peticiones (excepto registro y login) requieren autenticación mediante token. Incluir el header:
```
Authorization: Token <token>
```

## Base de Datos

Se utiliza SQLite por defecto. El archivo `db.sqlite3` se crea automáticamente al ejecutar las migraciones.

