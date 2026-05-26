from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import json


class User(AbstractUser):
    """Usuario personalizado con campos adicionales"""
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email
    
    def get_posts_count(self):
        """Obtener número de posts publicados"""
        return self.posts.filter(is_deleted=False).count()
    
    def get_comments_count(self):
        """Obtener número de comentarios realizados"""
        return self.comments.filter(is_deleted=False).count()
    
    def get_followers_count(self):
        """Obtener número de seguidores"""
        return self.followers.count()
    
    def get_following_count(self):
        """Obtener número de usuarios que sigue"""
        return self.following.count()
    
    def get_popularity_score(self):
        """Calcular puntuación de popularidad basada en actividad"""
        posts_count = self.get_posts_count()
        comments_count = self.get_comments_count()
        followers_count = self.get_followers_count()
        likes_received = PostLike.objects.filter(post__user=self).count()
        comments_received = Comment.objects.filter(post__user=self, is_deleted=False).count()
        
        # Fórmula: (posts * 2) + (comentarios * 1.5) + (seguidores * 3) + (likes recibidos * 1) + (comentarios recibidos * 2)
        score = (posts_count * 2) + (comments_count * 1.5) + (followers_count * 3) + (likes_received * 1) + (comments_received * 2)
        
        # Normalizar a porcentaje (0-100) basado en un máximo razonable
        # Asumimos que 1000 puntos = 100%
        max_score = 1000
        percentage = min((score / max_score) * 100, 100)
        return round(percentage, 1)
    
    def is_following(self, user):
        """Verificar si este usuario sigue a otro"""
        return self.following.filter(following=user).exists()
    
    def is_followed_by(self, user):
        """Verificar si otro usuario sigue a este"""
        return self.followers.filter(follower=user).exists()


class UserProfile(models.Model):
    """Perfil extendido del usuario"""
    GENDER_CHOICES = [
        ('Masculino', 'Masculino'),
        ('Femenino', 'Femenino'),
        ('Otro', 'Otro'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    height = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(300)])  # cm
    weight = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(500)])  # kg
    age = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(150)])
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, null=True, blank=True)
    body_fat_percentage = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    avatar_url = models.TextField(null=True, blank=True, help_text="URL o data URI del avatar del usuario (puede ser una imagen subida en base64, URL de avatar generado, etc.)")
    has_completed_onboarding = models.BooleanField(default=False)
    
    # Gamification - Fitness
    xp = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    current_streak = models.IntegerField(default=0)
    
    # Gamification - Nutrition
    nutrition_xp = models.IntegerField(default=0)
    nutrition_level = models.IntegerField(default=1)
    nutrition_streak = models.IntegerField(default=0)

    # Social / Identity
    bio = models.TextField(blank=True, null=True, help_text="Biografía o descripción del usuario")
    goals = models.JSONField(default=list, blank=True, help_text="Lista de metas (ej: ['Perder peso', 'Correr 5k'])")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.email}"


class MealPlan(models.Model):
    """Planes de alimentación"""
    CATEGORY_CHOICES = [
        ('Pérdida de Peso', 'Pérdida de Peso'),
        ('Aumento de Masa', 'Aumento de Masa'),
        ('Mantenimiento', 'Mantenimiento'),
        ('Vegetariano', 'Vegetariano'),
        ('Mediterráneo', 'Mediterráneo'),
        ('Equilibrado', 'Equilibrado'),
        ('Plan Personalizado', 'Plan Personalizado'),
    ]

    DIFFICULTY_CHOICES = [
        ('Fácil', 'Fácil'),
        ('Moderado', 'Moderado'),
        ('Avanzado', 'Avanzado'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meal_plans', null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    duration = models.CharField(max_length=50)  # "4 semanas"
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)
    image_url = models.URLField(blank=True, null=True)
    calories = models.CharField(max_length=50)  # "1800-2200 kcal"
    meals = models.JSONField(default=dict)  # {breakfast: [], lunch: [], dinner: [], snacks: []}
    benefits = models.JSONField(default=list)  # ["benefit1", "benefit2"]
    tips = models.JSONField(default=list)  # ["tip1", "tip2"]
    is_custom = models.BooleanField(default=False)  # True si fue creado por IA
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class NutritionEntry(models.Model):
    """Entradas de seguimiento nutricional"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='nutrition_entries')
    date = models.DateField()
    plan = models.ForeignKey(MealPlan, on_delete=models.SET_NULL, null=True, related_name='entries')
    meals = models.JSONField(default=dict)  # {breakfast: bool, lunch: bool, dinner: bool, snack: bool}
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.email} - {self.date}"


class ExerciseRoutine(models.Model):
    """Rutinas de ejercicio"""
    CATEGORY_CHOICES = [
        ('Definición', 'Definición'),
        ('Ganancia de Músculo', 'Ganancia de Músculo'),
        ('Cardio', 'Cardio'),
        ('Ejercicios Completos', 'Ejercicios Completos'),
        ('Rutina Personalizada', 'Rutina Personalizada'),
    ]

    DIFFICULTY_CHOICES = [
        ('Principiante', 'Principiante'),
        ('Intermedio', 'Intermedio'),
        ('Avanzado', 'Avanzado'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exercise_routines', null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)
    duration = models.CharField(max_length=50)  # "60 min"
    days_per_week = models.IntegerField(default=3)
    image_url = models.URLField(blank=True, null=True)
    exercises = models.JSONField(default=list)  # [{name, sets, reps, rest, description, imageUrl}]
    weekly_plan = models.JSONField(default=list)  # [{day, exercises, focus}]
    benefits = models.JSONField(default=list)
    tips = models.JSONField(default=list)
    is_custom = models.BooleanField(default=False)  # True si fue creado por IA
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class ExerciseEntry(models.Model):
    """Entradas de seguimiento de ejercicio"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exercise_entries')
    date = models.DateField()
    routine = models.ForeignKey(ExerciseRoutine, on_delete=models.SET_NULL, null=True, related_name='entries')
    exercises = models.JSONField(default=list)  # [{exerciseName, sets, reps, weight, completed}]
    duration = models.IntegerField(default=0)  # minutos
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.email} - {self.date}"


class MoodEntry(models.Model):
    """Entradas de seguimiento de ánimo"""
    MOOD_LEVELS = [
        (1, 'Muy malo'),
        (2, 'Malo'),
        (3, 'Regular'),
        (4, 'Bueno'),
        (5, 'Muy bueno'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mood_entries')
    date = models.DateField()
    mood = models.IntegerField(choices=MOOD_LEVELS)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.email} - {self.date} - Mood: {self.mood}"


class AISession(models.Model):
    """Sesiones de psicología con IA"""
    MOOD_LEVELS = [
        (1, 'Muy malo'),
        (2, 'Malo'),
        (3, 'Regular'),
        (4, 'Bueno'),
        (5, 'Muy bueno'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_sessions')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)
    mood_before = models.IntegerField(choices=MOOD_LEVELS)
    mood_after = models.IntegerField(choices=MOOD_LEVELS, null=True, blank=True)
    duration = models.IntegerField(default=0)  # minutos
    conversation_summary = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-start_time']

    def __str__(self):
        return f"{self.user.email} - {self.date} - {self.start_time}"


class HydrationEntry(models.Model):
    """Entradas de seguimiento de hidratación"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hydration_entries')
    date = models.DateField()
    amount = models.FloatField(default=0, validators=[MinValueValidator(0)])  # ml
    goal = models.FloatField(default=2000, validators=[MinValueValidator(0)])  # ml (default 2000ml = 2L)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.email} - {self.date} - {self.amount}ml"


class ChatMessage(models.Model):
    """Mensajes de chat con los asistentes de IA"""
    CHAT_TYPES = [
        ('psychology', 'Psicología'),
        ('nutrition', 'Nutrición'),
        ('exercise', 'Ejercicio'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    chat_type = models.CharField(max_length=20, choices=CHAT_TYPES)
    session_id = models.CharField(max_length=100, null=True, blank=True, help_text="ID de sesión para agrupar mensajes")
    text = models.TextField()
    is_bot = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True, help_text="Datos adicionales (plan_id, routine_id, etc.)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['user', 'chat_type', 'session_id']),
            models.Index(fields=['user', 'chat_type', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.chat_type} - {self.timestamp}"


# ============================================
# MODELOS DE COMUNIDAD
# ============================================

class Post(models.Model):
    """Publicaciones en la comunidad"""
    POST_CATEGORIES = [
        ('logro', 'Logro Personal'),
        ('consejo', 'Consejo'),
        ('experiencia', 'Experiencia Compartida'),
        ('pregunta', 'Pregunta'),
        ('motivacion', 'Motivación'),
        ('gratitud', 'Gratitud'),
    ]
    
    POST_DOMAINS = [
        ('psychology', 'Psicología'),
        ('nutrition', 'Nutrición'),
        ('exercise', 'Ejercicio'),
        ('general', 'General'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField(help_text="Contenido del post")
    category = models.CharField(max_length=20, choices=POST_CATEGORIES, default='experiencia')
    domain = models.CharField(max_length=20, choices=POST_DOMAINS, default='general')
    image_url = models.TextField(null=True, blank=True, help_text="URL o data URI de imagen opcional")
    is_anonymous = models.BooleanField(default=False, help_text="Si es True, el post se muestra como anónimo")
    likes_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['category', '-created_at']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"Post by {self.user.email} - {self.created_at}"


class Comment(models.Model):
    """Comentarios en posts"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    likes_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"Comment by {self.user.email} on post {self.post.id}"


class PostLike(models.Model):
    """Likes en posts"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['post', 'user']
        indexes = [
            models.Index(fields=['post', 'user']),
        ]
    
    def __str__(self):
        return f"Like by {self.user.email} on post {self.post.id}"


class CommentLike(models.Model):
    """Likes en comentarios"""
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comment_likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['comment', 'user']
        indexes = [
            models.Index(fields=['comment', 'user']),
        ]
    
    def __str__(self):
        return f"Like by {self.user.email} on comment {self.comment.id}"


class Achievement(models.Model):
    """Logros disponibles en la plataforma"""
    ACHIEVEMENT_TYPES = [
        ('streak', 'Racha'),
        ('entries', 'Entradas'),
        ('community', 'Comunidad'),
        ('milestone', 'Hito'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, help_text="Nombre del icono (ej: 'trophy.fill')")
    color = models.CharField(max_length=20, default='#FFD700', help_text="Color en hexadecimal")
    achievement_type = models.CharField(max_length=20, choices=ACHIEVEMENT_TYPES)
    requirement = models.IntegerField(default=1, help_text="Cantidad requerida para obtener el logro")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['achievement_type', 'requirement']
    
    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    """Logros obtenidos por usuarios"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, related_name='user_achievements')
    progress = models.IntegerField(default=0, help_text="Progreso actual hacia el logro")
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'achievement']
        indexes = [
            models.Index(fields=['user', 'is_completed']),
            models.Index(fields=['achievement', 'is_completed']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.achievement.name}"


class Notification(models.Model):
    """Notificaciones para usuarios"""
    NOTIFICATION_TYPES = [
        ('post_like', 'Like en Publicación'),
        ('post_comment', 'Comentario en Publicación'),
        ('comment_like', 'Like en Comentario'),
        ('achievement', 'Logro Desbloqueado'),
        ('user_follow', 'Nuevo Seguidor'),
        ('conversation_request', 'Invitación de Chat'),
        ('conversation_accepted', 'Invitación Aceptada'),
        ('chat_message', 'Nuevo Mensaje'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Referencias opcionales a objetos relacionados
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    
    # Usuario que generó la notificación (quien dio like, comentó, etc.)
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications_sent')
    
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"Notification for {self.user.email} - {self.notification_type}"


class SavedPost(models.Model):
    """Publicaciones guardadas por usuarios"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_posts')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='saved_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'post']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['post', 'user']),
        ]
    
    def __str__(self):
        return f"{self.user.email} saved post {self.post.id}"


class PostReport(models.Model):
    """Reportes de publicaciones"""
    REPORT_REASONS = [
        ('spam', 'Spam'),
        ('inappropriate', 'Contenido Inapropiado'),
        ('harassment', 'Acoso'),
        ('false_info', 'Información Falsa'),
        ('other', 'Otro'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('reviewed', 'Revisado'),
        ('resolved', 'Resuelto'),
        ('dismissed', 'Descartado'),
    ]
    
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reports')
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_reports')
    reason = models.CharField(max_length=20, choices=REPORT_REASONS)
    description = models.TextField(blank=True, null=True, help_text="Descripción adicional del reporte")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_reports')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True, null=True, help_text="Notas del administrador")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['reported_by', '-created_at']),
        ]
    
    def __str__(self):
        return f"Report on post {self.post.id} by {self.reported_by.email} - {self.reason}"


class UserFollow(models.Model):
    """Sistema de seguir/seguidores"""
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['follower', 'following']
        indexes = [
            models.Index(fields=['follower', '-created_at']),
            models.Index(fields=['following', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


class Conversation(models.Model):
    """Conversaciones entre usuarios que se siguen mutuamente"""
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('accepted', 'Aceptada'),
        ('rejected', 'Rechazada'),
        ('blocked', 'Bloqueada'),
    ]
    
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations_as_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations_as_user2')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    initiated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations_initiated')
    last_message_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user1', 'user2']
        indexes = [
            models.Index(fields=['user1', 'status', '-last_message_at']),
            models.Index(fields=['user2', 'status', '-last_message_at']),
            models.Index(fields=['status', '-last_message_at']),
        ]
    
    def __str__(self):
        return f"Conversation between {self.user1.username} and {self.user2.username}"
    
    def get_other_user(self, current_user):
        """Obtener el otro usuario de la conversación"""
        return self.user2 if self.user1 == current_user else self.user1
    
    def is_mutual_follow(self):
        """Verificar si ambos usuarios se siguen mutuamente"""
        return (
            UserFollow.objects.filter(follower=self.user1, following=self.user2).exists() and
            UserFollow.objects.filter(follower=self.user2, following=self.user1).exists()
        )


class DirectMessage(models.Model):
    """Mensajes directos en conversaciones entre usuarios"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='direct_messages_sent')
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['conversation', '-created_at']),
            models.Index(fields=['sender', '-created_at']),
            models.Index(fields=['is_read', '-created_at']),
        ]
    
    def __str__(self):
        return f"Message from {self.sender.username} in conversation {self.conversation.id}"


class GratitudeEntry(models.Model):
    """Entradas del diario de gratitud"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gratitude_entries')
    date = models.DateField(default=timezone.now)
    items = models.JSONField(default=list)  # ["item1", "item2", "item3"]
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['user', '-date']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.date}"


class PasswordResetCode(models.Model):
    """Códigos de verificación temporales de 6 dígitos para restablecer contraseñas"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_codes')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        # Válido por 15 minutos
        from django.utils import timezone
        from datetime import timedelta
        return timezone.now() > self.created_at + timedelta(minutes=15)

    def __str__(self):
        return f"Code for {self.user.email}: {self.code}"

