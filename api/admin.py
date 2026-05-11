from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    User, UserProfile, MealPlan, NutritionEntry,
    ExerciseRoutine, ExerciseEntry, MoodEntry,
    AISession, HydrationEntry, Post, Comment,
    PostLike, CommentLike, Achievement, UserAchievement,
    Notification, SavedPost, PostReport, UserFollow,
    Conversation, DirectMessage
)


# ============ INLINES (Datos relacionados) ============
class UserProfileInline(admin.StackedInline):
    """Inline para mostrar el perfil del usuario"""
    model = UserProfile
    can_delete = False
    verbose_name = "Perfil"
    verbose_name_plural = "Información del Perfil"
    fields = ('height', 'weight', 'age', 'gender', 'body_fat_percentage', 'has_completed_onboarding')
    readonly_fields = ('created_at', 'updated_at')


class MealPlanInline(admin.TabularInline):
    """Inline para mostrar planes de alimentación del usuario"""
    model = MealPlan
    extra = 0
    fields = ('title', 'category', 'difficulty', 'is_custom', 'created_at')
    readonly_fields = ('created_at',)
    show_change_link = True
    verbose_name = "Plan de Alimentación"
    verbose_name_plural = "Planes de Alimentación"


class NutritionEntryInline(admin.TabularInline):
    """Inline para mostrar entradas de seguimiento nutricional"""
    model = NutritionEntry
    extra = 0
    fields = ('date', 'plan', 'get_meals_summary', 'created_at')
    readonly_fields = ('get_meals_summary', 'created_at')
    show_change_link = True
    verbose_name = "Entrada Nutricional"
    verbose_name_plural = "Seguimiento Nutricional"
    ordering = ['-date']
    
    def get_meals_summary(self, obj):
        if isinstance(obj.meals, dict):
            completed = sum(1 for meal in ['breakfast', 'lunch', 'dinner', 'snack'] if obj.meals.get(meal, False))
            return f"{completed}/4 comidas"
        return '-'
    get_meals_summary.short_description = 'Comidas'


class ExerciseRoutineInline(admin.TabularInline):
    """Inline para mostrar rutinas de ejercicio del usuario"""
    model = ExerciseRoutine
    extra = 0
    fields = ('title', 'category', 'difficulty', 'days_per_week', 'is_custom', 'created_at')
    readonly_fields = ('created_at',)
    show_change_link = True
    verbose_name = "Rutina de Ejercicio"
    verbose_name_plural = "Rutinas de Ejercicio"


class ExerciseEntryInline(admin.TabularInline):
    """Inline para mostrar entradas de seguimiento de ejercicio"""
    model = ExerciseEntry
    extra = 0
    fields = ('date', 'routine', 'get_exercises_summary', 'duration', 'created_at')
    readonly_fields = ('get_exercises_summary', 'created_at')
    show_change_link = True
    verbose_name = "Entrada de Ejercicio"
    verbose_name_plural = "Seguimiento de Ejercicio"
    ordering = ['-date']
    
    def get_exercises_summary(self, obj):
        if isinstance(obj.exercises, list):
            completed = sum(1 for ex in obj.exercises if ex.get('completed', False))
            total = len(obj.exercises)
            return f"{completed}/{total} ejercicios"
        return '-'
    get_exercises_summary.short_description = 'Ejercicios'


class MoodEntryInline(admin.TabularInline):
    """Inline para mostrar entradas de ánimo"""
    model = MoodEntry
    extra = 0
    fields = ('date', 'get_mood_display', 'has_note', 'created_at')
    readonly_fields = ('get_mood_display', 'has_note', 'created_at')
    show_change_link = True
    verbose_name = "Entrada de Ánimo"
    verbose_name_plural = "Seguimiento de Ánimo"
    ordering = ['-date']
    
    def get_mood_display(self, obj):
        mood_labels = {1: 'Muy malo', 2: 'Malo', 3: 'Regular', 4: 'Bueno', 5: 'Muy bueno'}
        return mood_labels.get(obj.mood, f'Mood {obj.mood}')
    get_mood_display.short_description = 'Ánimo'
    
    def has_note(self, obj):
        return bool(obj.note)
    has_note.short_description = 'Tiene Nota'
    has_note.boolean = True


class AISessionInline(admin.TabularInline):
    """Inline para mostrar sesiones de IA"""
    model = AISession
    extra = 0
    fields = ('date', 'start_time', 'get_mood_before', 'get_mood_after', 'duration', 'created_at')
    readonly_fields = ('get_mood_before', 'get_mood_after', 'created_at')
    show_change_link = True
    verbose_name = "Sesión de IA"
    verbose_name_plural = "Sesiones de Psicología IA"
    ordering = ['-date', '-start_time']
    
    def get_mood_before(self, obj):
        mood_labels = {1: 'Muy malo', 2: 'Malo', 3: 'Regular', 4: 'Bueno', 5: 'Muy bueno'}
        return mood_labels.get(obj.mood_before, f'Mood {obj.mood_before}')
    get_mood_before.short_description = 'Ánimo Antes'
    
    def get_mood_after(self, obj):
        if obj.mood_after:
            mood_labels = {1: 'Muy malo', 2: 'Malo', 3: 'Regular', 4: 'Bueno', 5: 'Muy bueno'}
            return mood_labels.get(obj.mood_after, f'Mood {obj.mood_after}')
        return '-'
    get_mood_after.short_description = 'Ánimo Después'


class HydrationEntryInline(admin.TabularInline):
    """Inline para mostrar entradas de hidratación"""
    model = HydrationEntry
    extra = 0
    fields = ('date', 'amount', 'goal', 'get_percentage', 'created_at')
    readonly_fields = ('get_percentage', 'created_at')
    show_change_link = True
    verbose_name = "Entrada de Hidratación"
    verbose_name_plural = "Seguimiento de Hidratación"
    ordering = ['-date']
    
    def get_percentage(self, obj):
        if obj.goal > 0:
            percentage = (obj.amount / obj.goal) * 100
            return f"{percentage:.0f}%"
        return '-'
    get_percentage.short_description = 'Progreso'


# ============ USER ADMIN CON INLINES ============
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'get_profile_summary', 'get_stats_summary', 'is_staff', 'is_superuser', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'date_joined', 'created_at']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-date_joined']
    readonly_fields = ['date_joined', 'last_login', 'created_at', 'updated_at', 'get_profile_link', 'get_stats_dashboard']
    
    # Agregar inlines para mostrar datos relacionados
    inlines = [
        UserProfileInline,
        MealPlanInline,
        NutritionEntryInline,
        ExerciseRoutineInline,
        ExerciseEntryInline,
        MoodEntryInline,
        AISessionInline,
        HydrationEntryInline,
    ]
    
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Información Personal', {'fields': ('first_name', 'last_name')}),
        ('Permisos', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Enlaces Rápidos', {
            'fields': ('get_profile_link',),
            'classes': ('collapse',),
        }),
        ('Estadísticas', {
            'fields': ('get_stats_dashboard',),
            'classes': ('collapse',),
        }),
        ('Fechas Importantes', {'fields': ('date_joined', 'last_login', 'created_at', 'updated_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )
    
    def get_profile_link(self, obj):
        """Enlace al perfil del usuario"""
        try:
            profile = obj.profile
            url = reverse('admin:api_userprofile_change', args=[profile.pk])
            return format_html('<a href="{}" class="button">Ver Perfil Completo</a>', url)
        except UserProfile.DoesNotExist:
            return format_html('<span style="color: red;">Sin perfil - <a href="{}">Crear perfil</a></span>', 
                             reverse('admin:api_userprofile_add') + f'?user={obj.pk}')
    get_profile_link.short_description = 'Perfil'
    
    def get_profile_summary(self, obj):
        """Resumen del perfil en la lista"""
        try:
            profile = obj.profile
            info = []
            if profile.height:
                info.append(f"{profile.height}cm")
            if profile.weight:
                info.append(f"{profile.weight}kg")
            if profile.age:
                info.append(f"{profile.age}años")
            return ", ".join(info) if info else "Sin datos"
        except UserProfile.DoesNotExist:
            return "Sin perfil"
    get_profile_summary.short_description = 'Perfil'
    
    def get_stats_summary(self, obj):
        """Resumen de estadísticas en la lista"""
        stats = []
        stats.append(f"Planes: {obj.meal_plans.count()}")
        stats.append(f"Rutinas: {obj.exercise_routines.count()}")
        stats.append(f"Entradas: {obj.nutrition_entries.count()}")
        return " | ".join(stats)
    get_stats_summary.short_description = 'Estadísticas'
    
    def get_stats_dashboard(self, obj):
        """Dashboard de estadísticas en el detalle"""
        if not obj.pk:
            return "Guarda el usuario primero para ver estadísticas"
        
        stats_html = f"""
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 20px 0;">
            <div style="background: #e3f2fd; padding: 15px; border-radius: 5px;">
                <h4 style="margin: 0 0 10px 0;">📊 Perfil</h4>
                <p style="margin: 5px 0;"><strong>Altura:</strong> {obj.profile.height if hasattr(obj, 'profile') and obj.profile.height else 'N/A'} cm</p>
                <p style="margin: 5px 0;"><strong>Peso:</strong> {obj.profile.weight if hasattr(obj, 'profile') and obj.profile.weight else 'N/A'} kg</p>
                <p style="margin: 5px 0;"><strong>Edad:</strong> {obj.profile.age if hasattr(obj, 'profile') and obj.profile.age else 'N/A'} años</p>
            </div>
            <div style="background: #f3e5f5; padding: 15px; border-radius: 5px;">
                <h4 style="margin: 0 0 10px 0;">🍽️ Nutrición</h4>
                <p style="margin: 5px 0;"><strong>Planes:</strong> {obj.meal_plans.count()}</p>
                <p style="margin: 5px 0;"><strong>Entradas:</strong> {obj.nutrition_entries.count()}</p>
                <p style="margin: 5px 0;"><strong>Última entrada:</strong> {obj.nutrition_entries.first().date if obj.nutrition_entries.exists() else 'N/A'}</p>
            </div>
            <div style="background: #e8f5e9; padding: 15px; border-radius: 5px;">
                <h4 style="margin: 0 0 10px 0;">💪 Ejercicio</h4>
                <p style="margin: 5px 0;"><strong>Rutinas:</strong> {obj.exercise_routines.count()}</p>
                <p style="margin: 5px 0;"><strong>Sesiones:</strong> {obj.exercise_entries.count()}</p>
                <p style="margin: 5px 0;"><strong>Última sesión:</strong> {obj.exercise_entries.first().date if obj.exercise_entries.exists() else 'N/A'}</p>
            </div>
            <div style="background: #fff3e0; padding: 15px; border-radius: 5px;">
                <h4 style="margin: 0 0 10px 0;">😊 Ánimo</h4>
                <p style="margin: 5px 0;"><strong>Entradas:</strong> {obj.mood_entries.count()}</p>
                <p style="margin: 5px 0;"><strong>Promedio:</strong> {sum(e.mood for e in obj.mood_entries.all()) / obj.mood_entries.count() if obj.mood_entries.exists() else 'N/A'}</p>
            </div>
            <div style="background: #fce4ec; padding: 15px; border-radius: 5px;">
                <h4 style="margin: 0 0 10px 0;">🤖 IA Sessions</h4>
                <p style="margin: 5px 0;"><strong>Sesiones:</strong> {obj.ai_sessions.count()}</p>
                <p style="margin: 5px 0;"><strong>Última:</strong> {obj.ai_sessions.first().date if obj.ai_sessions.exists() else 'N/A'}</p>
            </div>
            <div style="background: #e0f2f1; padding: 15px; border-radius: 5px;">
                <h4 style="margin: 0 0 10px 0;">💧 Hidratación</h4>
                <p style="margin: 5px 0;"><strong>Entradas:</strong> {obj.hydration_entries.count()}</p>
                <p style="margin: 5px 0;"><strong>Promedio:</strong> {sum(e.amount for e in obj.hydration_entries.all()) / obj.hydration_entries.count() if obj.hydration_entries.exists() else 'N/A'} ml</p>
            </div>
        </div>
        """
        return format_html(stats_html)
    get_stats_dashboard.short_description = 'Dashboard de Estadísticas'


# ============ USER PROFILE ADMIN ============
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = [
        'get_user_email', 'get_user_username', 'height', 'weight', 
        'age', 'gender', 'body_fat_percentage', 'has_completed_onboarding', 
        'created_at'
    ]
    list_filter = ['gender', 'has_completed_onboarding', 'created_at', 'updated_at']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['created_at', 'updated_at', 'get_user_link']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Usuario', {
            'fields': ('user', 'get_user_link')
        }),
        ('Información Física', {
            'fields': ('height', 'weight', 'age', 'gender', 'body_fat_percentage'),
            'description': 'Altura en cm, peso en kg, edad en años'
        }),
        ('Estado', {
            'fields': ('has_completed_onboarding',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'Email'
    get_user_email.admin_order_field = 'user__email'
    
    def get_user_username(self, obj):
        return obj.user.username
    get_user_username.short_description = 'Username'
    get_user_username.admin_order_field = 'user__username'
    
    def get_user_link(self, obj):
        if obj.pk:
            url = reverse('admin:api_user_change', args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return '-'
    get_user_link.short_description = 'Usuario'


# ============ MEAL PLAN ADMIN ============
@admin.register(MealPlan)
class MealPlanAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'category', 'difficulty', 'get_user_email', 
        'is_custom', 'get_calories', 'created_at'
    ]
    list_filter = ['category', 'difficulty', 'is_custom', 'created_at', 'updated_at']
    search_fields = ['title', 'description', 'user__email', 'user__username']
    readonly_fields = ['created_at', 'updated_at', 'get_user_link']
    ordering = ['-created_at']
    list_per_page = 25
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('title', 'description', 'user', 'get_user_link', 'is_custom')
        }),
        ('Clasificación', {
            'fields': ('category', 'difficulty', 'duration', 'calories')
        }),
        ('Contenido', {
            'fields': ('image_url', 'meals', 'benefits', 'tips'),
            'description': 'Meals, benefits y tips son campos JSON'
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_user_email(self, obj):
        if obj.user:
            return obj.user.email
        return 'Plan Público'
    get_user_email.short_description = 'Usuario'
    get_user_email.admin_order_field = 'user__email'
    
    def get_user_link(self, obj):
        if obj.user:
            url = reverse('admin:api_user_change', args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return 'Plan Público'
    get_user_link.short_description = 'Usuario'
    
    def get_calories(self, obj):
        return obj.calories or '-'
    get_calories.short_description = 'Calorías'


# ============ NUTRITION ENTRY ADMIN ============
@admin.register(NutritionEntry)
class NutritionEntryAdmin(admin.ModelAdmin):
    list_display = [
        'get_user_email', 'date', 'get_plan_title', 
        'get_meals_completed', 'created_at'
    ]
    list_filter = ['date', 'created_at', 'updated_at', 'plan__category']
    search_fields = ['user__email', 'user__username', 'plan__title', 'note']
    readonly_fields = ['created_at', 'updated_at', 'get_user_link', 'get_plan_link']
    ordering = ['-date', '-created_at']
    date_hierarchy = 'date'
    list_per_page = 30
    
    fieldsets = (
        ('Usuario y Plan', {
            'fields': ('user', 'get_user_link', 'plan', 'get_plan_link', 'date')
        }),
        ('Comidas', {
            'fields': ('meals',),
            'description': 'JSON con breakfast, lunch, dinner, snack (booleanos)'
        }),
        ('Notas', {
            'fields': ('note',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'Usuario'
    get_user_email.admin_order_field = 'user__email'
    
    def get_user_link(self, obj):
        if obj.pk:
            url = reverse('admin:api_user_change', args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return '-'
    get_user_link.short_description = 'Usuario'
    
    def get_plan_title(self, obj):
        if obj.plan:
            url = reverse('admin:api_mealplan_change', args=[obj.plan.pk])
            return format_html('<a href="{}">{}</a>', url, obj.plan.title)
        return '-'
    get_plan_title.short_description = 'Plan'
    
    def get_plan_link(self, obj):
        return self.get_plan_title(obj)
    get_plan_link.short_description = 'Plan de Alimentación'
    
    def get_meals_completed(self, obj):
        if isinstance(obj.meals, dict):
            completed = sum(1 for meal in ['breakfast', 'lunch', 'dinner', 'snack'] if obj.meals.get(meal, False))
            total = 4
            percentage = (completed / total) * 100
            percentage_str = f"{percentage:.0f}"
            color = 'green' if percentage >= 75 else 'orange' if percentage >= 50 else 'red'
            return format_html(
                '<span style="color: {};">{}/{} ({}%)</span>',
                color, completed, total, percentage_str
            )
        return '-'
    get_meals_completed.short_description = 'Comidas Completadas'


# ============ EXERCISE ROUTINE ADMIN ============
@admin.register(ExerciseRoutine)
class ExerciseRoutineAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'category', 'difficulty', 'get_user_email',
        'days_per_week', 'duration', 'is_custom', 'created_at'
    ]
    list_filter = ['category', 'difficulty', 'is_custom', 'days_per_week', 'created_at', 'updated_at']
    search_fields = ['title', 'description', 'user__email', 'user__username']
    readonly_fields = ['created_at', 'updated_at', 'get_user_link', 'get_exercises_count']
    ordering = ['-created_at']
    list_per_page = 25
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('title', 'description', 'user', 'get_user_link', 'is_custom')
        }),
        ('Clasificación', {
            'fields': ('category', 'difficulty', 'duration', 'days_per_week')
        }),
        ('Contenido', {
            'fields': ('image_url', 'exercises', 'weekly_plan', 'benefits', 'tips'),
            'description': 'Exercises, weekly_plan, benefits y tips son campos JSON'
        }),
        ('Estadísticas', {
            'fields': ('get_exercises_count',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_user_email(self, obj):
        if obj.user:
            return obj.user.email
        return 'Rutina Pública'
    get_user_email.short_description = 'Usuario'
    get_user_email.admin_order_field = 'user__email'
    
    def get_user_link(self, obj):
        if obj.user:
            url = reverse('admin:api_user_change', args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return 'Rutina Pública'
    get_user_link.short_description = 'Usuario'
    
    def get_exercises_count(self, obj):
        if isinstance(obj.exercises, list):
            return f"{len(obj.exercises)} ejercicios"
        return '0 ejercicios'
    get_exercises_count.short_description = 'Número de Ejercicios'


# ============ EXERCISE ENTRY ADMIN ============
@admin.register(ExerciseEntry)
class ExerciseEntryAdmin(admin.ModelAdmin):
    list_display = [
        'get_user_email', 'date', 'get_routine_title',
        'get_exercises_completed', 'duration', 'created_at'
    ]
    list_filter = ['date', 'created_at', 'updated_at', 'routine__category']
    search_fields = ['user__email', 'user__username', 'routine__title', 'notes']
    readonly_fields = ['created_at', 'updated_at', 'get_user_link', 'get_routine_link']
    ordering = ['-date', '-created_at']
    date_hierarchy = 'date'
    list_per_page = 30
    
    fieldsets = (
        ('Usuario y Rutina', {
            'fields': ('user', 'get_user_link', 'routine', 'get_routine_link', 'date')
        }),
        ('Ejercicios', {
            'fields': ('exercises',),
            'description': 'JSON con lista de ejercicios completados'
        }),
        ('Duración y Notas', {
            'fields': ('duration', 'notes')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'Usuario'
    get_user_email.admin_order_field = 'user__email'
    
    def get_user_link(self, obj):
        if obj.pk:
            url = reverse('admin:api_user_change', args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return '-'
    get_user_link.short_description = 'Usuario'
    
    def get_routine_title(self, obj):
        if obj.routine:
            url = reverse('admin:api_exerciseroutine_change', args=[obj.routine.pk])
            return format_html('<a href="{}">{}</a>', url, obj.routine.title)
        return '-'
    get_routine_title.short_description = 'Rutina'
    
    def get_routine_link(self, obj):
        return self.get_routine_title(obj)
    get_routine_link.short_description = 'Rutina de Ejercicio'
    
    def get_exercises_completed(self, obj):
        if isinstance(obj.exercises, list):
            completed = sum(1 for ex in obj.exercises if ex.get('completed', False))
            total = len(obj.exercises)
            if total > 0:
                percentage = (completed / total) * 100
                percentage_str = f"{percentage:.0f}"
                color = 'green' if percentage >= 75 else 'orange' if percentage >= 50 else 'red'
                return format_html(
                    '<span style="color: {};">{}/{} ({}%)</span>',
                    color, completed, total, percentage_str
                )
        return '-'
    get_exercises_completed.short_description = 'Ejercicios Completados'


# ============ MOOD ENTRY ADMIN ============
@admin.register(MoodEntry)
class MoodEntryAdmin(admin.ModelAdmin):
    list_display = [
        'get_user_email', 'date', 'get_mood_display', 
        'has_note', 'created_at'
    ]
    list_filter = ['mood', 'date', 'created_at', 'updated_at']
    search_fields = ['user__email', 'user__username', 'note']
    readonly_fields = ['created_at', 'updated_at', 'get_user_link']
    ordering = ['-date', '-created_at']
    date_hierarchy = 'date'
    list_per_page = 30
    
    fieldsets = (
        ('Usuario', {
            'fields': ('user', 'get_user_link', 'date')
        }),
        ('Estado de Ánimo', {
            'fields': ('mood', 'note')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'Email'
    get_user_email.admin_order_field = 'user__email'
    
    def get_user_link(self, obj):
        if obj.pk:
            url = reverse('admin:api_user_change', args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return '-'
    get_user_link.short_description = 'Usuario'
    
    def get_mood_display(self, obj):
        mood_colors = {
            1: 'red',
            2: 'orange',
            3: 'yellow',
            4: 'lightgreen',
            5: 'green'
        }
        mood_labels = {
            1: 'Muy malo',
            2: 'Malo',
            3: 'Regular',
            4: 'Bueno',
            5: 'Muy bueno'
        }
        color = mood_colors.get(obj.mood, 'gray')
        label = mood_labels.get(obj.mood, f'Mood {obj.mood}')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, label
        )
    get_mood_display.short_description = 'Estado de Ánimo'
    
    def has_note(self, obj):
        return bool(obj.note)
    has_note.short_description = 'Tiene Nota'
    has_note.boolean = True


# ============ AI SESSION ADMIN ============
@admin.register(AISession)
class AISessionAdmin(admin.ModelAdmin):
    list_display = [
        'get_user_email', 'date', 'start_time', 
        'get_mood_before', 'get_mood_after', 
        'get_duration_display', 'created_at'
    ]
    list_filter = ['date', 'created_at', 'mood_before', 'mood_after']
    search_fields = ['user__email', 'user__username', 'conversation_summary']
    readonly_fields = ['created_at', 'updated_at', 'get_user_link']
    ordering = ['-date', '-start_time']
    date_hierarchy = 'date'
    list_per_page = 30
    
    fieldsets = (
        ('Usuario', {
            'fields': ('user', 'get_user_link', 'date')
        }),
        ('Sesión', {
            'fields': ('start_time', 'end_time', 'duration')
        }),
        ('Estado de Ánimo', {
            'fields': ('mood_before', 'mood_after')
        }),
        ('Resumen', {
            'fields': ('conversation_summary',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'Usuario'
    get_user_email.admin_order_field = 'user__email'
    
    def get_user_link(self, obj):
        if obj.pk:
            url = reverse('admin:api_user_change', args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return '-'
    get_user_link.short_description = 'Usuario'
    
    def get_mood_before(self, obj):
        mood_labels = {1: 'Muy malo', 2: 'Malo', 3: 'Regular', 4: 'Bueno', 5: 'Muy bueno'}
        return mood_labels.get(obj.mood_before, f'Mood {obj.mood_before}')
    get_mood_before.short_description = 'Ánimo Antes'
    
    def get_mood_after(self, obj):
        if obj.mood_after:
            mood_labels = {1: 'Muy malo', 2: 'Malo', 3: 'Regular', 4: 'Bueno', 5: 'Muy bueno'}
            return mood_labels.get(obj.mood_after, f'Mood {obj.mood_after}')
        return '-'
    get_mood_after.short_description = 'Ánimo Después'
    
    def get_duration_display(self, obj):
        if obj.duration:
            return f"{obj.duration} min"
        return '-'
    get_duration_display.short_description = 'Duración'


# ============ HYDRATION ENTRY ADMIN ============
@admin.register(HydrationEntry)
class HydrationEntryAdmin(admin.ModelAdmin):
    list_display = [
        'get_user_email', 'date', 'get_amount_display',
        'get_goal_display', 'get_percentage', 'created_at'
    ]
    list_filter = ['date', 'created_at', 'updated_at']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['created_at', 'updated_at', 'get_user_link', 'get_percentage_display']
    ordering = ['-date', '-created_at']
    date_hierarchy = 'date'
    list_per_page = 30
    
    fieldsets = (
        ('Usuario', {
            'fields': ('user', 'get_user_link', 'date')
        }),
        ('Hidratación', {
            'fields': ('amount', 'goal', 'get_percentage_display')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'Usuario'
    get_user_email.admin_order_field = 'user__email'
    
    def get_user_link(self, obj):
        if obj.pk:
            url = reverse('admin:api_user_change', args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return '-'
    get_user_link.short_description = 'Usuario'
    
    def get_amount_display(self, obj):
        return f"{obj.amount} ml"
    get_amount_display.short_description = 'Cantidad'
    get_amount_display.admin_order_field = 'amount'
    
    def get_goal_display(self, obj):
        return f"{obj.goal} ml"
    get_goal_display.short_description = 'Meta'
    get_goal_display.admin_order_field = 'goal'
    
    def get_percentage(self, obj):
        if obj.goal > 0:
            percentage = (obj.amount / obj.goal) * 100
            percentage_str = f"{percentage:.0f}"
            color = 'green' if percentage >= 100 else 'orange' if percentage >= 75 else 'red'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}%</span>',
                color, percentage_str
            )
        return '-'
    get_percentage.short_description = 'Progreso'
    get_percentage.admin_order_field = 'amount'
    
    def get_percentage_display(self, obj):
        return self.get_percentage(obj)
    get_percentage_display.short_description = 'Porcentaje de Meta'


# ============ COMMUNITY MODELS ADMIN ============
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_user_email', 'get_content_preview', 'category', 'is_anonymous', 'likes_count', 'comments_count', 'created_at']
    list_filter = ['category', 'is_anonymous', 'is_deleted', 'created_at']
    search_fields = ['content', 'user__email', 'user__username']
    readonly_fields = ['created_at', 'updated_at', 'likes_count', 'comments_count']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    def get_user_email(self, obj):
        if obj.is_anonymous:
            return 'Anónimo'
        return obj.user.email
    get_user_email.short_description = 'Usuario'
    
    def get_content_preview(self, obj):
        preview = obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
        return preview
    get_content_preview.short_description = 'Contenido'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_post_id', 'get_user_email', 'get_content_preview', 'likes_count', 'created_at']
    list_filter = ['is_deleted', 'created_at']
    search_fields = ['content', 'user__email', 'user__username', 'post__content']
    readonly_fields = ['created_at', 'updated_at', 'likes_count']
    ordering = ['-created_at']
    
    def get_post_id(self, obj):
        return obj.post.id
    get_post_id.short_description = 'Post ID'
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'Usuario'
    
    def get_content_preview(self, obj):
        preview = obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
        return preview
    get_content_preview.short_description = 'Contenido'


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_post_id', 'get_user_email', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'user__username', 'post__content']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_post_id(self, obj):
        return obj.post.id
    get_post_id.short_description = 'Post ID'
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'Usuario'


@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_comment_id', 'get_user_email', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'user__username', 'comment__content']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_comment_id(self, obj):
        return obj.comment.id
    get_comment_id.short_description = 'Comentario ID'
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'Usuario'


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['name', 'achievement_type', 'requirement', 'is_active', 'created_at']
    list_filter = ['achievement_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']
    ordering = ['achievement_type', 'requirement']


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ['get_user_email', 'get_achievement_name', 'progress', 'is_completed', 'completed_at', 'created_at']
    list_filter = ['is_completed', 'achievement__achievement_type', 'created_at']
    search_fields = ['user__email', 'user__username', 'achievement__name']
    readonly_fields = ['created_at', 'completed_at']
    ordering = ['-created_at']
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'Usuario'
    
    def get_achievement_name(self, obj):
        return obj.achievement.name
    get_achievement_name.short_description = 'Logro'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_user_email', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__email', 'user__username', 'title', 'message']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'Usuario'


@admin.register(SavedPost)
class SavedPostAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_user_email', 'get_post_id', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'user__username', 'post__content']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'Usuario'
    
    def get_post_id(self, obj):
        return obj.post.id
    get_post_id.short_description = 'Post ID'


@admin.register(PostReport)
class PostReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_post_id', 'get_reported_by', 'reason', 'status', 'created_at']
    list_filter = ['reason', 'status', 'created_at']
    search_fields = ['post__content', 'reported_by__email', 'description']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    list_editable = ['status']
    
    def get_post_id(self, obj):
        return obj.post.id
    get_post_id.short_description = 'Post ID'
    
    def get_reported_by(self, obj):
        return obj.reported_by.email
    get_reported_by.short_description = 'Reportado por'


@admin.register(UserFollow)
class UserFollowAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_follower_email', 'get_following_email', 'created_at']
    list_filter = ['created_at']
    search_fields = ['follower__email', 'follower__username', 'following__email', 'following__username']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_follower_email(self, obj):
        return obj.follower.email
    get_follower_email.short_description = 'Seguidor'
    
    def get_following_email(self, obj):
        return obj.following.email
    get_following_email.short_description = 'Sigue a'


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user1', 'user2', 'status', 'initiated_by', 'last_message_at', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user1__email', 'user1__username', 'user2__email', 'user2__username']
    readonly_fields = ['created_at', 'updated_at', 'last_message_at']
    ordering = ['-last_message_at', '-created_at']


@admin.register(DirectMessage)
class DirectMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_conversation_id', 'sender', 'get_content_preview', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['content', 'sender__email', 'sender__username', 'conversation__id']
    readonly_fields = ['created_at', 'updated_at', 'read_at']
    ordering = ['-created_at']
    
    def get_conversation_id(self, obj):
        return obj.conversation.id
    get_conversation_id.short_description = 'Conversación'
    
    def get_content_preview(self, obj):
        preview = obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
        return preview
    get_content_preview.short_description = 'Contenido'

