from rest_framework import serializers
import math
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from .models import (
    User, UserProfile, MealPlan, NutritionEntry,
    ExerciseRoutine, ExerciseEntry, MoodEntry,
    AISession, HydrationEntry, ChatMessage as AIChatMessage,
    Post, Comment, PostLike, CommentLike,
    Achievement, UserAchievement, Notification,
    SavedPost, PostReport, UserFollow, Conversation, DirectMessage,
    GratitudeEntry
)


def validate_password_custom(value):
    """Validador personalizado de contraseña (mínimo 6 caracteres)"""
    if len(value) < 6:
        raise ValidationError('La contraseña debe tener al menos 6 caracteres.')
    return value


class UserSerializer(serializers.ModelSerializer):
    """Serializer para el modelo User"""
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'date_joined', 'created_at', 'updated_at']
        read_only_fields = ['id', 'date_joined', 'created_at', 'updated_at']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer para el perfil de usuario"""
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'height', 'weight', 'age', 'gender',
            'body_fat_percentage', 'avatar_url', 'has_completed_onboarding',
            'xp', 'level', 'current_streak',
            'nutrition_xp', 'nutrition_level', 'nutrition_streak',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer para registro de usuarios"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password_custom])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password2']

    def validate_email(self, value):
        """Validar que el email no esté registrado"""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Este correo electrónico ya está registrado.")
        return value.lower()

    def validate_username(self, value):
        """Validar que el username no esté en uso"""
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Este nombre de usuario ya está en uso.")
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password']
        )
        # Crear perfil automáticamente
        UserProfile.objects.create(user=user)
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer para login"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'), username=email, password=password)
            if not user:
                raise serializers.ValidationError('Correo electrónico o contraseña incorrectos.')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Debe incluir "email" y "password".')
        return attrs


class MealPlanSerializer(serializers.ModelSerializer):
    """Serializer para planes de alimentación"""
    class Meta:
        model = MealPlan
        fields = [
            'id', 'user', 'title', 'description', 'category', 'duration',
            'difficulty', 'image_url', 'calories', 'meals', 'benefits',
            'tips', 'is_custom', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NutritionEntrySerializer(serializers.ModelSerializer):
    """Serializer para entradas de seguimiento nutricional"""
    plan_title = serializers.CharField(source='plan.title', read_only=True)
    plan_category = serializers.CharField(source='plan.category', read_only=True)

    class Meta:
        model = NutritionEntry
        fields = [
            'id', 'user', 'date', 'plan', 'plan_title', 'plan_category',
            'meals', 'note', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class ExerciseRoutineSerializer(serializers.ModelSerializer):
    """Serializer para rutinas de ejercicio"""
    class Meta:
        model = ExerciseRoutine
        fields = [
            'id', 'user', 'title', 'description', 'category', 'difficulty',
            'duration', 'days_per_week', 'image_url', 'exercises', 'weekly_plan',
            'benefits', 'tips', 'is_custom', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ExerciseEntrySerializer(serializers.ModelSerializer):
    """Serializer para entradas de seguimiento de ejercicio"""
    routine_name = serializers.CharField(source='routine.title', read_only=True)

    class Meta:
        model = ExerciseEntry
        fields = [
            'id', 'user', 'date', 'routine', 'routine_name', 'exercises',
            'duration', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class MoodEntrySerializer(serializers.ModelSerializer):
    """Serializer para entradas de ánimo"""
    
    def validate_mood(self, value):
        """Validar que el mood esté en el rango correcto"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("El estado de ánimo debe estar entre 1 y 5")
        return value
    
    class Meta:
        model = MoodEntry
        fields = ['id', 'user', 'date', 'mood', 'note', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class AISessionSerializer(serializers.ModelSerializer):
    """Serializer para sesiones de IA"""
    class Meta:
        model = AISession
        fields = [
            'id', 'user', 'date', 'start_time', 'end_time',
            'mood_before', 'mood_after', 'duration', 'conversation_summary',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class HydrationEntrySerializer(serializers.ModelSerializer):
    """Serializer para entradas de hidratación"""
    class Meta:
        model = HydrationEntry
        fields = ['id', 'user', 'date', 'amount', 'goal', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer para mensajes de chat"""
    class Meta:
        model = AIChatMessage
        fields = [
            'id', 'user', 'chat_type', 'session_id', 'text', 'is_bot',
            'timestamp', 'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'timestamp', 'created_at']


# ============================================
# SERIALIZERS DE COMUNIDAD
# ============================================

class CommentSerializer(serializers.ModelSerializer):
    """Serializer para comentarios"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_avatar = serializers.CharField(source='user.profile.avatar_url', read_only=True, allow_null=True)
    is_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'post', 'user', 'user_username', 'user_avatar',
            'content', 'likes_count', 'is_liked', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'likes_count', 'created_at', 'updated_at']
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False


class PostSerializer(serializers.ModelSerializer):
    """Serializer para posts"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_avatar = serializers.CharField(source='user.profile.avatar_url', read_only=True, allow_null=True)
    is_liked = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    comments_preview = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = [
            'id', 'user', 'user_username', 'user_avatar', 'content', 'category',
            'image_url', 'is_anonymous', 'likes_count', 'comments_count',
            'is_liked', 'is_saved', 'comments_preview', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'likes_count', 'comments_count', 'created_at', 'updated_at']
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False
    
    def get_is_saved(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            from .models import SavedPost
            return SavedPost.objects.filter(user=request.user, post=obj).exists()
        return False
    
    def get_comments_preview(self, obj):
        """Retornar solo los últimos 3 comentarios para preview"""
        comments = obj.comments.filter(is_deleted=False).order_by('-created_at')[:3]
        return CommentSerializer(comments, many=True, context=self.context).data


class PostLikeSerializer(serializers.ModelSerializer):
    """Serializer para likes en posts"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = PostLike
        fields = ['id', 'post', 'user', 'user_username', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class CommentLikeSerializer(serializers.ModelSerializer):
    """Serializer para likes en comentarios"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = CommentLike
        fields = ['id', 'comment', 'user', 'user_username', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class AchievementSerializer(serializers.ModelSerializer):
    """Serializer para logros"""
    class Meta:
        model = Achievement
        fields = [
            'id', 'name', 'description', 'icon', 'color',
            'achievement_type', 'requirement', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class UserAchievementSerializer(serializers.ModelSerializer):
    """Serializer para logros de usuarios"""
    achievement = AchievementSerializer(read_only=True)
    achievement_name = serializers.CharField(source='achievement.name', read_only=True)
    achievement_icon = serializers.CharField(source='achievement.icon', read_only=True)
    achievement_color = serializers.CharField(source='achievement.color', read_only=True)
    
    class Meta:
        model = UserAchievement
        fields = [
            'id', 'user', 'achievement', 'achievement_name', 'achievement_icon',
            'achievement_color', 'progress', 'is_completed', 'completed_at', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer para notificaciones"""
    from_user_username = serializers.CharField(source='from_user.username', read_only=True, allow_null=True)
    from_user_avatar = serializers.CharField(source='from_user.profile.avatar_url', read_only=True, allow_null=True)
    post_id = serializers.IntegerField(source='post.id', read_only=True, allow_null=True)
    comment_id = serializers.IntegerField(source='comment.id', read_only=True, allow_null=True)
    achievement_name = serializers.CharField(source='achievement.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'notification_type', 'title', 'message',
            'from_user', 'from_user_username', 'from_user_avatar',
            'post', 'post_id', 'comment', 'comment_id', 'achievement', 'achievement_name',
            'is_read', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']


class SavedPostSerializer(serializers.ModelSerializer):
    """Serializer para publicaciones guardadas"""
    post = PostSerializer(read_only=True)
    post_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = SavedPost
        fields = ['id', 'user', 'post', 'post_id', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class PostReportSerializer(serializers.ModelSerializer):
    """Serializer para reportes de publicaciones"""
    reported_by_username = serializers.CharField(source='reported_by.username', read_only=True)
    post_title = serializers.CharField(source='post.content', read_only=True)
    reviewed_by_username = serializers.CharField(source='reviewed_by.username', read_only=True, allow_null=True)

    class Meta:
        model = PostReport
        fields = [
            'id', 'post', 'reported_by', 'reported_by_username', 'reason', 'description',
            'status', 'reviewed_by', 'reviewed_by_username', 'reviewed_at', 'admin_notes',
            'created_at', 'updated_at', 'post_title'
        ]
        read_only_fields = [
            'id', 'reported_by', 'reported_by_username', 'status', 'reviewed_by',
            'reviewed_by_username', 'reviewed_at', 'created_at', 'updated_at', 'post_title'
        ]


class UserFollowSerializer(serializers.ModelSerializer):
    """Serializer para seguir/seguidores"""
    follower_username = serializers.CharField(source='follower.username', read_only=True)
    follower_avatar = serializers.CharField(source='follower.profile.avatar_url', read_only=True, allow_null=True)
    following_username = serializers.CharField(source='following.username', read_only=True)
    following_avatar = serializers.CharField(source='following.profile.avatar_url', read_only=True, allow_null=True)

    class Meta:
        model = UserFollow
        fields = [
            'id', 'follower', 'follower_username', 'follower_avatar',
            'following', 'following_username', 'following_avatar', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class UserProfileDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para perfil de usuario con estadísticas"""
    user = UserSerializer(read_only=True)
    posts_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    popularity_score = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()

    is_followed_by = serializers.SerializerMethodField()
    
    # Lazy backfill fields
    xp = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()
    nutrition_xp = serializers.SerializerMethodField()
    nutrition_level = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'height', 'weight', 'age', 'gender',
            'body_fat_percentage', 'avatar_url', 'has_completed_onboarding',
            'bio', 'goals',
            'xp', 'level', 'current_streak',
            'nutrition_xp', 'nutrition_level', 'nutrition_streak',
            'posts_count', 'comments_count', 'followers_count', 'following_count',
            'popularity_score', 'is_following', 'is_followed_by',
            'exercise_stats', 'nutrition_stats',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    # Custom stats fields
    exercise_stats = serializers.SerializerMethodField()
    nutrition_stats = serializers.SerializerMethodField()

    def get_exercise_stats(self, obj):
        entries = ExerciseEntry.objects.filter(user=obj.user)
        total_workouts = entries.count()
        total_minutes = sum(entry.duration for entry in entries)
        
        # Calculate weekly frequency (approximate)
        if total_workouts > 0:
            first_entry = entries.order_by('date').first()
            if first_entry:
                from django.utils import timezone
                days_active = (timezone.now().date() - first_entry.date).days + 1
                weeks_active = max(1, days_active / 7)
                weekly_frequency = round(total_workouts / weeks_active, 1)
            else:
                weekly_frequency = 0
        else:
            weekly_frequency = 0
            
        return {
            'totalWorkouts': total_workouts,
            'totalMinutes': total_minutes,
            'weeklyFrequency': weekly_frequency
        }

    def get_nutrition_stats(self, obj):
        # Calculate meals logged
        entries = NutritionEntry.objects.filter(user=obj.user)
        total_meals = 0
        for entry in entries:
            meals = entry.meals if isinstance(entry.meals, dict) else {}
            # Count boolean true or objects with completed=true
            for v in meals.values():
                if isinstance(v, bool) and v:
                    total_meals += 1
                elif isinstance(v, dict) and v.get('completed'):
                    total_meals += 1
        
        # Water Average (last 30 days)
        from django.utils import timezone
        from datetime import timedelta
        last_30_days = timezone.now().date() - timedelta(days=30)
        hydration_entries = HydrationEntry.objects.filter(user=obj.user, date__gte=last_30_days)
        total_water = sum(entry.amount for entry in hydration_entries)
        days_with_water = hydration_entries.count()
        water_avg = total_water / days_with_water if days_with_water > 0 else 0
        
        # Weekly adherence (placeholder logic or simplified)
        weekly_adherence = 0 
        
        return {
            'mealsLogged': total_meals,
            'waterAverage': round(water_avg),
            'weeklyAdherence': weekly_adherence
        }

    def get_xp(self, obj):
        if obj.xp > 0:
            return obj.xp
        
        # Backfill XP from ExerciseEntry
        entries = ExerciseEntry.objects.filter(user=obj.user)
        total_xp = 0
        for entry in entries:
            # XP = duration * 8 + exercises_count * 20
            duration_xp = entry.duration * 8
            
            # Ensure exercises is a list and count only completed ones
            exercises_list = entry.exercises if isinstance(entry.exercises, list) else []
            completed_exercises = 0
            
            for ex in exercises_list:
                if isinstance(ex, dict) and ex.get('completed'):
                    completed_exercises += 1
            
            exercises_xp = completed_exercises * 20
            total_xp += duration_xp + exercises_xp
        
        if total_xp > 0:
            obj.xp = total_xp
            # Update level
            obj.level = math.floor(total_xp / 1000) + 1
            obj.save(update_fields=['xp', 'level'])
            
        return total_xp

    def get_level(self, obj):
        # Trigger get_xp to ensure backfill
        if obj.xp == 0:
            self.get_xp(obj)
        return obj.level

    def get_nutrition_xp(self, obj):
        if obj.nutrition_xp > 0:
            return obj.nutrition_xp
            
        # Backfill Nutrition XP
        entries = NutritionEntry.objects.filter(user=obj.user)
        total_xp = 0
        for entry in entries:
            meals = entry.meals if isinstance(entry.meals, dict) else {}
            completed_count = sum(1 for v in meals.values() if v)
            entry_xp = completed_count * 15
            if completed_count >= 4: # Assuming 4 meals is daily goal
                entry_xp += 100
            total_xp += entry_xp
            
        if total_xp > 0:
            obj.nutrition_xp = total_xp
            obj.nutrition_level = math.floor(total_xp / 1000) + 1
            obj.save(update_fields=['nutrition_xp', 'nutrition_level'])
            
        return total_xp

    def get_nutrition_level(self, obj):
        if obj.nutrition_xp == 0:
            self.get_nutrition_xp(obj)
        return obj.nutrition_level

    def get_xp(self, obj):
        if obj.xp > 0:
            return obj.xp
        
        # Backfill XP from ExerciseEntry
        entries = ExerciseEntry.objects.filter(user=obj.user)
        total_xp = 0
        for entry in entries:
            # XP = duration * 8 + exercises_count * 20
            duration_xp = entry.duration * 8
            exercises_count = len(entry.exercises) if isinstance(entry.exercises, list) else 0
            exercises_xp = exercises_count * 20
            total_xp += duration_xp + exercises_xp
        
        if total_xp > 0:
            obj.xp = total_xp
            # Update level
            obj.level = math.floor(total_xp / 1000) + 1
            obj.save(update_fields=['xp', 'level'])
            
        return total_xp

    def get_level(self, obj):
        # Trigger get_xp to ensure backfill
        if obj.xp == 0:
            self.get_xp(obj)
        return obj.level

    def get_nutrition_xp(self, obj):
        if obj.nutrition_xp > 0:
            return obj.nutrition_xp
            
        # Backfill Nutrition XP
        entries = NutritionEntry.objects.filter(user=obj.user)
        total_xp = 0
        for entry in entries:
            meals = entry.meals if isinstance(entry.meals, dict) else {}
            completed_count = sum(1 for v in meals.values() if v)
            entry_xp = completed_count * 15
            if completed_count >= 4: # Assuming 4 meals is daily goal
                entry_xp += 100
            total_xp += entry_xp
            
        if total_xp > 0:
            obj.nutrition_xp = total_xp
            obj.nutrition_level = math.floor(total_xp / 1000) + 1
            obj.save(update_fields=['nutrition_xp', 'nutrition_level'])
            
        return total_xp

    def get_nutrition_level(self, obj):
        if obj.nutrition_xp == 0:
            self.get_nutrition_xp(obj)
        return obj.nutrition_level

    def get_posts_count(self, obj):
        return obj.user.get_posts_count()

    def get_comments_count(self, obj):
        return obj.user.get_comments_count()

    def get_followers_count(self, obj):
        return obj.user.get_followers_count()

    def get_following_count(self, obj):
        return obj.user.get_following_count()

    def get_popularity_score(self, obj):
        return obj.user.get_popularity_score()

    def get_is_following(self, obj):
        """Verificar si el usuario actual sigue a este usuario"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.is_following(obj.user)
        return False

    def get_is_followed_by(self, obj):
        """Verificar si este usuario sigue al usuario actual"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.user.is_following(request.user)
        return False


class ConversationSerializer(serializers.ModelSerializer):
    """Serializer para conversaciones"""
    user1_username = serializers.CharField(source='user1.username', read_only=True)
    user1_avatar = serializers.CharField(source='user1.profile.avatar_url', read_only=True, allow_null=True)
    user2_username = serializers.CharField(source='user2.username', read_only=True)
    user2_avatar = serializers.CharField(source='user2.profile.avatar_url', read_only=True, allow_null=True)
    initiated_by_username = serializers.CharField(source='initiated_by.username', read_only=True)
    other_user = serializers.SerializerMethodField()
    other_user_username = serializers.SerializerMethodField()
    other_user_avatar = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id', 'user1', 'user1_username', 'user1_avatar',
            'user2', 'user2_username', 'user2_avatar',
            'initiated_by', 'initiated_by_username',
            'status', 'other_user', 'other_user_username', 'other_user_avatar',
            'last_message', 'unread_count', 'last_message_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_message_at']

    def get_other_user(self, obj):
        """Obtener el otro usuario de la conversación"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.get_other_user(request.user).id
        return None

    def get_other_user_username(self, obj):
        """Obtener el username del otro usuario"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.get_other_user(request.user).username
        return None

    def get_other_user_avatar(self, obj):
        """Obtener el avatar del otro usuario"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            other_user = obj.get_other_user(request.user)
            if hasattr(other_user, 'profile'):
                return other_user.profile.avatar_url
        return None

    def get_last_message(self, obj):
        """Obtener el último mensaje de la conversación"""
        from .models import DirectMessage
        last_msg = DirectMessage.objects.filter(conversation=obj).order_by('-created_at').first()
        if last_msg:
            return {
                'id': last_msg.id,
                'content': last_msg.content,
                'sender': last_msg.sender.id,
                'sender_username': last_msg.sender.username,
                'created_at': last_msg.created_at.isoformat(),
            }
        return None

    def get_unread_count(self, obj):
        """Obtener el número de mensajes no leídos"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.messages.filter(is_read=False).exclude(sender=request.user).count()
        return 0


class DirectMessageSerializer(serializers.ModelSerializer):
    """Serializer para mensajes directos entre usuarios"""
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    sender_avatar = serializers.CharField(source='sender.profile.avatar_url', read_only=True, allow_null=True)
    conversation_id = serializers.IntegerField(source='conversation.id', read_only=True)

    class Meta:
        model = DirectMessage
        fields = [
            'id', 'conversation', 'conversation_id', 'sender', 'sender_username', 'sender_avatar',
            'content', 'is_read', 'read_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'sender', 'is_read', 'read_at', 'created_at', 'updated_at']


class GratitudeEntrySerializer(serializers.ModelSerializer):
    """Serializer para entradas del diario de gratitud"""
    class Meta:
        model = GratitudeEntry
        fields = ['id', 'user', 'date', 'items', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

