from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, AuthViewSet, UserProfileViewSet,
    MealPlanViewSet, NutritionEntryViewSet,
    ExerciseRoutineViewSet, ExerciseEntryViewSet,
    MoodEntryViewSet, AISessionViewSet, HydrationEntryViewSet,
    AIChatMessageViewSet,
    PostViewSet, CommentViewSet, AchievementViewSet, UserAchievementViewSet,
    NotificationViewSet, SavedPostViewSet, PostReportViewSet, UserFollowViewSet,
    ConversationViewSet, DirectMessageViewSet, GratitudeEntryViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'profiles', UserProfileViewSet, basename='profile')
router.register(r'meal-plans', MealPlanViewSet, basename='mealplan')
router.register(r'nutrition-entries', NutritionEntryViewSet, basename='nutritionentry')
router.register(r'exercise-routines', ExerciseRoutineViewSet, basename='exerciseroutine')
router.register(r'exercise-entries', ExerciseEntryViewSet, basename='exerciseentry')
router.register(r'mood-entries', MoodEntryViewSet, basename='moodentry')
router.register(r'ai-sessions', AISessionViewSet, basename='aisession')
router.register(r'hydration-entries', HydrationEntryViewSet, basename='hydrationentry')
router.register(r'chat-messages', AIChatMessageViewSet, basename='aichatmessage')
router.register(r'gratitude-entries', GratitudeEntryViewSet, basename='gratitudeentry')
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'direct-messages', DirectMessageViewSet, basename='directmessage')
router.register(r'posts', PostViewSet, basename='post')
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'achievements', AchievementViewSet, basename='achievement')
router.register(r'user-achievements', UserAchievementViewSet, basename='userachievement')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'saved-posts', SavedPostViewSet, basename='savedpost')
router.register(r'post-reports', PostReportViewSet, basename='postreport')
router.register(r'follows', UserFollowViewSet, basename='userfollow')

urlpatterns = [
    path('', include(router.urls)),
]

