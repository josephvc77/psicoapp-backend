# 🚀 Inicio Rápido - PsicoApp Backend

## ⚡ Inicio Rápido (Primera vez)

```bash
# 1. Navegar a la carpeta
cd PsicoAppBackend

# 2. Activar entorno virtual
source venv/bin/activate  # macOS/Linux
# O en Windows: venv\Scripts\activate

# 3. Instalar dependencias (solo primera vez)
pip install -r requirements.txt

# 4. Ejecutar migraciones (solo primera vez)
python manage.py migrate

# 5. Crear superusuario (OBLIGATORIO para admin)
python manage.py createsuperuser
# Ingresa: Email, Username, Password

# 6. Iniciar servidor
python manage.py runserver
```

## ✅ Verificar que funciona

1. **Servidor corriendo**: Abre `http://localhost:8000` - deberías ver una página de Django
2. **Admin funcionando**: Abre `http://localhost:8000/admin` - deberías ver el login
3. **API funcionando**: Abre `http://localhost:8000/api/` - deberías ver la lista de endpoints

## 📊 ¿Qué se guarda automáticamente?

Cuando los usuarios usen la app, se guardará automáticamente en la base de datos:

✅ **Cuentas de usuario** → Tabla `User`
✅ **Perfiles de usuario** → Tabla `UserProfile` (altura, peso, edad, etc.)
✅ **Planes de alimentación** → Tabla `MealPlan` (incluyendo planes creados por IA)
✅ **Seguimiento nutricional** → Tabla `NutritionEntry` (comidas completadas por día)
✅ **Rutinas de ejercicio** → Tabla `ExerciseRoutine` (incluyendo rutinas personalizadas por IA)
✅ **Seguimiento de ejercicio** → Tabla `ExerciseEntry` (sesiones de entrenamiento)
✅ **Seguimiento de ánimo** → Tabla `MoodEntry` (estado emocional diario)
✅ **Sesiones de psicología** → Tabla `AISession` (chats con psicólogo IA)
✅ **Hidratación** → Tabla `HydrationEntry` (consumo de agua diario)

## 🔍 Ver los datos guardados

1. Inicia sesión en el admin: `http://localhost:8000/admin`
2. Navega por los diferentes modelos en el menú lateral
3. Usa los filtros y búsquedas para encontrar información específica

## 🛠️ Comandos útiles

```bash
# Ver todos los usuarios
python manage.py shell
>>> from api.models import User
>>> User.objects.all()

# Ver estadísticas
>>> from api.models import *
>>> User.objects.count()  # Número de usuarios
>>> MealPlan.objects.filter(is_custom=True).count()  # Planes personalizados
>>> ExerciseRoutine.objects.filter(is_custom=True).count()  # Rutinas personalizadas

# Salir del shell
>>> exit()
```

## ⚠️ Importante

- **Base de datos**: SQLite (archivo `db.sqlite3`) - se crea automáticamente
- **Puerto**: 8000 por defecto (cambiar si está ocupado)
- **CORS**: Habilitado para desarrollo (cambiar en producción)
- **Token Auth**: Los tokens se generan automáticamente al registrar/iniciar sesión

## 🐛 Problemas comunes

**Error: "Port 8000 already in use"**
```bash
python manage.py runserver 8001
# Luego actualiza la URL en PsicoApp/services/apiService.ts
```

**Error: "No module named 'django'"**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**Error: "Table doesn't exist"**
```bash
python manage.py migrate
```

