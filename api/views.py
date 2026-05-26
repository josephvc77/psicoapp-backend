from rest_framework import viewsets, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import login
from django.utils import timezone
from django.db.models import Q
from django.db import models
from datetime import date, timedelta
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import (
    User, UserProfile, MealPlan, NutritionEntry,
    ExerciseRoutine, ExerciseEntry, MoodEntry,
    AISession, HydrationEntry, ChatMessage as AIChatMessage,
    Post, Comment, PostLike, CommentLike,
    Achievement, UserAchievement, Notification,
    SavedPost, PostReport, UserFollow, Conversation, DirectMessage, GratitudeEntry, PasswordResetCode
)
from .serializers import (
    UserSerializer, UserProfileSerializer, UserProfileDetailSerializer, RegisterSerializer,
    LoginSerializer, MealPlanSerializer, NutritionEntrySerializer,
    ExerciseRoutineSerializer, ExerciseEntrySerializer,
    MoodEntrySerializer, AISessionSerializer, HydrationEntrySerializer,
    ChatMessageSerializer as AIChatMessageSerializer,
    PostSerializer, CommentSerializer, PostLikeSerializer,
    CommentLikeSerializer, AchievementSerializer, UserAchievementSerializer,
    NotificationSerializer, SavedPostSerializer, PostReportSerializer,
    NotificationSerializer, SavedPostSerializer, PostReportSerializer,
    UserFollowSerializer, ConversationSerializer, DirectMessageSerializer,
    GratitudeEntrySerializer
)


# ============================================
# FUNCIÓN HELPER PARA ACTUALIZAR LOGROS
# ============================================
def update_achievements(user, achievement_type, progress_increment=1):
    """Actualizar logros de un usuario basado en su actividad"""
    try:
        # Obtener logros activos del tipo especificado
        achievements = Achievement.objects.filter(
            achievement_type=achievement_type,
            is_active=True
        )
        
        for achievement in achievements:
            # Obtener o crear el UserAchievement
            user_achievement, created = UserAchievement.objects.get_or_create(
                user=user,
                achievement=achievement
            )
            
            # Actualizar progreso
            if not user_achievement.is_completed:
                user_achievement.progress += progress_increment
                
                # Verificar si se completó el logro
                if user_achievement.progress >= achievement.requirement:
                    user_achievement.is_completed = True
                    user_achievement.completed_at = timezone.now()
                    
                    # Crear notificación para el logro completado
                    Notification.objects.create(
                        user=user,
                        notification_type='achievement',
                        title='¡Logro Desbloqueado!',
                        message=f'Has desbloqueado el logro: {achievement.name}',
                        achievement=achievement
                    )
                
                user_achievement.save()
    except Exception as e:
        print(f"[Achievements] Error updating achievements: {e}")


# ============================================
# FUNCIÓN HELPER PARA NOTIFICACIONES EN TIEMPO REAL
# ============================================
def send_notification_realtime(notification):
    """Enviar notificación a través de WebSocket"""
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            # Serializar la notificación manualmente (sin contexto de request)
            notification_data = {
                'id': notification.id,
                'user': notification.user.id,
                'notification_type': notification.notification_type,
                'title': notification.title,
                'message': notification.message,
                'from_user': notification.from_user.id if notification.from_user else None,
                'from_user_username': notification.from_user.username if notification.from_user else None,
                'from_user_avatar': notification.from_user.profile.avatar_url if notification.from_user and hasattr(notification.from_user, 'profile') else None,
                'post': notification.post.id if notification.post else None,
                'post_id': notification.post.id if notification.post else None,
                'comment': notification.comment.id if notification.comment else None,
                'comment_id': notification.comment.id if notification.comment else None,
                'achievement': notification.achievement.id if notification.achievement else None,
                'achievement_name': notification.achievement.name if notification.achievement else None,
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat() if notification.created_at else None,
            }
            
            # Enviar al grupo del usuario
            async_to_sync(channel_layer.group_send)(
                f'notifications_{notification.user.id}',
                {
                    'type': 'notification_created',
                    'notification': notification_data
                }
            )
            
            # Actualizar contador de no leídas
            unread_count = Notification.objects.filter(
                user=notification.user,
                is_read=False
            ).count()
            
            async_to_sync(channel_layer.group_send)(
                f'notifications_{notification.user.id}',
                {
                    'type': 'unread_count_update',
                    'count': unread_count
                }
            )
            if __debug__:
                print(f"[WebSocket] Notificación enviada a usuario {notification.user.id}")
    except Exception as e:
        print(f"[WebSocket] Error enviando notificación: {e}")
        import traceback
        traceback.print_exc()


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet para usuarios"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Obtener información del usuario actual"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


def send_ikigai_email(subject, template_type, context, to_email):
    """Enviar correos electrónicos con formato HTML premium para Ikigai App"""
    from django.core.mail import EmailMultiAlternatives
    from django.conf import settings
    
    username = context.get('username', 'Usuario')
    
    if template_type == 'forgot_password':
        code = context.get('code')
        text_content = f"""
Hola, {username}.

Hemos recibido una solicitud para restablecer la contraseña de tu cuenta en Ikigai App.

Tu código de recuperación es: {code}

Este código es válido por 15 minutos. Si no solicitaste este cambio, puedes ignorar este correo de forma segura.

Saludos cordiales,
Soporte de Ikigai App
ikigai.app.support@gmail.com
"""
        html_content = f"""
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Código de Recuperación - Ikigai App</title>
</head>
<body style="margin:0;padding:0;background-color:#F3F4F6;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;">
  <table border="0" cellpadding="0" cellspacing="0" width="100%" style="table-layout:fixed;background-color:#F3F4F6;">
    <tr>
      <td align="center" style="padding:40px 0;">
        <table border="0" cellpadding="0" cellspacing="0" width="500" style="background-color:#FFFFFF;border-radius:24px;overflow:hidden;box-shadow:0 10px 15px -3px rgba(0,0,0,0.1),0 4px 6px -2px rgba(0,0,0,0.05);">
          <tr>
            <td align="center" style="background:linear-gradient(135deg, #8B5CF6 0%, #3B82F6 100%);padding:40px 30px;">
              <table border="0" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="center">
                    <div style="width:70px;height:70px;background-color:rgba(255,255,255,0.2);border-radius:20px;display:inline-block;line-height:70px;text-align:center;font-size:32px;color:#FFFFFF;font-weight:bold;box-shadow:0 8px 16px rgba(0,0,0,0.1);">
                      息
                    </div>
                  </td>
                </tr>
                <tr>
                  <td align="center" style="padding-top:16px;">
                    <h1 style="margin:0;font-size:26px;color:#FFFFFF;font-weight:700;letter-spacing:-0.5px;">Ikigai App</h1>
                    <p style="margin:4px 0 0 0;font-size:14px;color:rgba(255,255,255,0.8);font-style:italic;">Encuentra tu equilibrio. Vive con propósito.</p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:40px 32px;background-color:#FFFFFF;">
              <h2 style="margin:0 0 16px 0;font-size:20px;color:#1F2937;font-weight:700;">¡Hola, {username}!</h2>
              <p style="margin:0 0 24px 0;font-size:15px;color:#4B5563;line-height:24px;">Hemos recibido una solicitud para restablecer la contraseña de tu cuenta. Entendemos perfectamente lo importante que es tu tranquilidad, por lo que hemos generado el siguiente código temporal de verificación:</p>
              
              <table border="0" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom:28px;">
                <tr>
                  <td align="center" style="background-color:#F3F4F6;border-radius:16px;padding:24px 16px;border:1px dashed #D1D5DB;">
                    <span style="font-size:13px;color:#6B7280;text-transform:uppercase;letter-spacing:1px;font-weight:600;display:block;margin-bottom:8px;">Código de Verificación</span>
                    <span style="font-size:36px;color:#3B82F6;font-weight:800;letter-spacing:6px;display:block;font-family:'Courier New',Courier,monospace;">{code}</span>
                  </td>
                </tr>
              </table>
              
              <p style="margin:0 0 24px 0;font-size:14px;color:#6B7280;line-height:22px;background-color:#EFF6FF;border-left:4px solid #3B82F6;padding:12px 16px;border-radius:0 8px 8px 0;">
                <strong>Importante:</strong> Este código expira en <strong>15 minutos</strong> por motivos de seguridad. Si tú no has realizado esta solicitud, puedes ignorar este correo con total tranquilidad; tu cuenta sigue estando protegida.
              </p>
              <hr style="border:0;border-top:1px solid #E5E7EB;margin:32px 0 24px 0;">
              <p style="margin:0;font-size:13px;color:#9CA3AF;line-height:20px;text-align:center;">Este es un correo automático. Por favor, no respondas a este mensaje.<br>Soporte y Ayuda: <a href="mailto:ikigai.app.support@gmail.com" style="color:#3B82F6;text-decoration:none;font-weight:600;">ikigai.app.support@gmail.com</a></p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""
    elif template_type == 'password_changed':
        datetime_str = context.get('datetime_str')
        text_content = f"""
Hola, {username}.

Te informamos que la contraseña de tu cuenta de Ikigai App ha sido cambiada exitosamente.

Detalles del cambio:
• Estado: Completado con éxito
• Fecha y hora: {datetime_str} UTC

¿No reconoces esta actividad? Si tú no has realizado este cambio de contraseña, por favor ponte en contacto con nuestro equipo de soporte de forma inmediata a través del correo ikigai.app.support@gmail.com para proteger tu información.

Saludos cordiales,
Soporte de Ikigai App
ikigai.app.support@gmail.com
"""
        html_content = f"""
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Seguridad: Contraseña Actualizada - Ikigai App</title>
</head>
<body style="margin:0;padding:0;background-color:#F3F4F6;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;">
  <table border="0" cellpadding="0" cellspacing="0" width="100%" style="table-layout:fixed;background-color:#F3F4F6;">
    <tr>
      <td align="center" style="padding:40px 0;">
        <table border="0" cellpadding="0" cellspacing="0" width="500" style="background-color:#FFFFFF;border-radius:24px;overflow:hidden;box-shadow:0 10px 15px -3px rgba(0,0,0,0.1),0 4px 6px -2px rgba(0,0,0,0.05);">
          <tr>
            <td align="center" style="background:linear-gradient(135deg, #10B981 0%, #059669 100%);padding:40px 30px;">
              <table border="0" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="center">
                    <div style="width:70px;height:70px;background-color:rgba(255,255,255,0.2);border-radius:20px;display:inline-block;line-height:70px;text-align:center;font-size:32px;color:#FFFFFF;font-weight:bold;box-shadow:0 8px 16px rgba(0,0,0,0.1);">
                      ✓
                    </div>
                  </td>
                </tr>
                <tr>
                  <td align="center" style="padding-top:16px;">
                    <h1 style="margin:0;font-size:26px;color:#FFFFFF;font-weight:700;letter-spacing:-0.5px;">Ikigai App</h1>
                    <p style="margin:4px 0 0 0;font-size:14px;color:rgba(255,255,255,0.8);font-style:italic;">Tu cuenta está segura y al día.</p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:40px 32px;background-color:#FFFFFF;">
              <h2 style="margin:0 0 16px 0;font-size:20px;color:#1F2937;font-weight:700;">¡Hola, {username}!</h2>
              <p style="margin:0 0 20px 0;font-size:15px;color:#4B5563;line-height:24px;">Te informamos que <strong>la contraseña de tu cuenta de Ikigai App ha sido cambiada exitosamente</strong>.</p>
              
              <table border="0" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom:28px;">
                <tr>
                  <td style="background-color:#ECFDF5;border-radius:16px;padding:20px;border:1px solid #A7F3D0;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%">
                      <tr>
                        <td style="font-size:14px;color:#065F46;line-height:22px;">
                          <strong>Detalles del cambio:</strong><br>
                          • Estado: Completado con éxito<br>
                          • Fecha y hora: {datetime_str} UTC
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
              
              <p style="margin:0 0 24px 0;font-size:14px;color:#EF4444;line-height:22px;background-color:#FEF2F2;border-left:4px solid #EF4444;padding:12px 16px;border-radius:0 8px 8px 0;">
                <strong>¿No reconoces esta actividad?</strong> Si tú no has realizado este cambio de contraseña, por favor ponte en contacto con nuestro equipo de soporte de forma inmediata a través del correo <a href="mailto:ikigai.app.support@gmail.com" style="color:#EF4444;text-decoration:underline;font-weight:600;">ikigai.app.support@gmail.com</a> para proteger tu información.
              </p>
              <hr style="border:0;border-top:1px solid #E5E7EB;margin:32px 0 24px 0;">
              <p style="margin:0;font-size:13px;color:#9CA3AF;line-height:20px;text-align:center;">Este es un correo automático de seguridad.<br>Soporte y Ayuda: <a href="mailto:ikigai.app.support@gmail.com" style="color:#059669;text-decoration:none;font-weight:600;">ikigai.app.support@gmail.com</a></p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""
    else:
        return False
        
    msg = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [to_email]
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=False)
    return True


class AuthViewSet(viewsets.ViewSet):
    """ViewSet para autenticación"""
    permission_classes = [AllowAny]
    authentication_classes = [TokenAuthentication] # Use TokenAuthentication to enable request.user while bypassing CSRF checks on login/register


    @action(detail=False, methods=['post'])
    def register(self, request):
        """Registro de nuevo usuario"""
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'success': True,
                'user': UserSerializer(user).data,
                'token': token.key
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def login(self, request):
        """Inicio de sesión"""
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'success': True,
                'user': UserSerializer(user).data,
                'token': token.key
            })
        return Response({
            'success': False,
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """Cerrar sesión"""
        try:
            request.user.auth_token.delete()
        except:
            pass
        return Response({'success': True})

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def check_email(self, request):
        """Verificar si un email ya está registrado"""
        email = request.data.get('email', '').lower().strip()
        if not email:
            return Response({'exists': False}, status=status.HTTP_400_BAD_REQUEST)
        
        exists = User.objects.filter(email__iexact=email).exists()
        return Response({'exists': exists})

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def check_username(self, request):
        """Verificar si un username ya está en uso"""
        username = request.data.get('username', '').strip()
        if not username:
            return Response({'exists': False}, status=status.HTTP_400_BAD_REQUEST)
        
        exists = User.objects.filter(username__iexact=username).exists()
        return Response({'exists': exists})

    @action(detail=False, methods=['post'], permission_classes=[AllowAny], url_path='forgot-password')
    def forgot_password(self, request):
        """Generar código de verificación de 6 dígitos y enviarlo por correo"""
        email = request.data.get('email', '').lower().strip()
        if not email:
            return Response({
                'success': False,
                'error': 'El campo "email" es requerido.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'No existe un usuario registrado con este correo electrónico.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Generar código aleatorio de 6 dígitos
        import random
        code = f"{random.randint(100000, 999999)}"
        
        # Guardar en base de datos
        PasswordResetCode.objects.create(user=user, code=code)
        
        try:
            send_ikigai_email(
                'Código de Recuperación de Contraseña - Ikigai App',
                'forgot_password',
                {
                    'username': user.username or 'Usuario',
                    'code': code
                },
                user.email
            )
            return Response({
                'success': True,
                'message': 'Se ha enviado un código de recuperación a tu correo electrónico.'
            })
        except Exception as e:
            # Fallback en desarrollo para mostrar el código si no hay internet / SMTP no configurado
            print(f"[Email Error] No se pudo enviar el correo: {e}")
            return Response({
                'success': True,
                'message': 'Se generó el código con éxito (modo desarrollo/consola). Por favor revisa la consola del servidor.',
                'dev_code': code  # Proporcionar el código en la respuesta si falla el email, excelente para testing local sin credenciales
            })

    @action(detail=False, methods=['post'], permission_classes=[AllowAny], url_path='reset-password')
    def reset_password(self, request):
        """Restablecer contraseña usando el código recibido"""
        email = request.data.get('email', '').lower().strip()
        code = request.data.get('code', '').strip()
        new_password = request.data.get('password', '').strip()
        
        if not email or not code or not new_password:
            return Response({
                'success': False,
                'error': 'Los campos "email", "code" y "password" son obligatorios.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Usuario no encontrado.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Buscar el último código activo para el usuario
        reset_code = PasswordResetCode.objects.filter(
            user=user,
            code=code,
            is_used=False
        ).order_by('-created_at').first()
        
        if not reset_code:
            return Response({
                'success': False,
                'error': 'El código ingresado es incorrecto o ya ha sido utilizado.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if reset_code.is_expired():
            return Response({
                'success': False,
                'error': 'El código ha expirado. Por favor, solicita uno nuevo.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Actualizar contraseña
        user.set_password(new_password)
        user.save()
        
        # Marcar código como usado
        reset_code.is_used = True
        reset_code.save()
        
        # Enviar email de notificación de contraseña actualizada
        try:
            from django.utils import timezone
            send_ikigai_email(
                'Seguridad: Contraseña Actualizada - Ikigai App',
                'password_changed',
                {
                    'username': user.username or 'Usuario',
                    'datetime_str': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                },
                user.email
            )
        except Exception as e:
            print(f"[Email Error] No se pudo enviar el correo de confirmación: {e}")
        
        return Response({
            'success': True,
            'message': 'Tu contraseña ha sido restablecida con éxito.'
        })

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated], url_path='change-password')
    def change_password(self, request):
        """Cambiar contraseña de usuario autenticado"""
        old_password = request.data.get('old_password', '').strip()
        new_password = request.data.get('new_password', '').strip()
        
        if not old_password or not new_password:
            return Response({
                'success': False,
                'error': 'Los campos "old_password" y "new_password" son obligatorios.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        if not user.check_password(old_password):
            return Response({
                'success': False,
                'error': 'La contraseña actual es incorrecta.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(new_password)
        user.save()
        
        # Enviar email de confirmación
        try:
            from django.utils import timezone
            send_ikigai_email(
                'Seguridad: Contraseña Actualizada - Ikigai App',
                'password_changed',
                {
                    'username': user.username or 'Usuario',
                    'datetime_str': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                },
                user.email
            )
        except Exception as e:
            print(f"[Email Error] No se pudo enviar el correo de confirmación: {e}")
        
        return Response({
            'success': True,
            'message': 'Contraseña actualizada con éxito.'
        })




class UserProfileViewSet(viewsets.ModelViewSet):
    """ViewSet para perfiles de usuario"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        """Obtener perfil del usuario actual con estadísticas"""
        try:
            profile = UserProfile.objects.get(user=request.user)
            serializer = UserProfileDetailSerializer(profile, context={'request': request})
            return Response({
                'success': True,
                'data': serializer.data
            })
        except UserProfile.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Perfil no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'], url_path='detail')
    def detail(self, request, pk=None):
        """Obtener perfil detallado de otro usuario"""
        try:
            profile = self.get_object()
            serializer = UserProfileDetailSerializer(profile, context={'request': request})
            return Response({
                'success': True,
                'data': serializer.data
            })
        except UserProfile.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Perfil no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'], url_path='user/(?P<user_id>[^/.]+)')
    def by_user_id(self, request, user_id=None):
        """Obtener perfil por ID de usuario"""
        try:
            user = User.objects.get(id=user_id)
            profile, created = UserProfile.objects.get_or_create(user=user)
            serializer = UserProfileDetailSerializer(profile, context={'request': request})
            return Response({
                'success': True,
                'data': serializer.data
            })
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Usuario no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        """Obtener o actualizar el perfil del usuario actual"""
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        if request.method == 'GET':
            # Usar el serializer detallado para GET
            serializer = UserProfileDetailSerializer(profile, context={'request': request})
            return Response({
                'success': True,
                'data': serializer.data
            })
        else:
            serializer = self.get_serializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True,
                    'data': serializer.data
                })
            return Response({
                'success': False,
                'error': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)


class MealPlanViewSet(viewsets.ModelViewSet):
    """ViewSet para planes de alimentación"""
    serializer_class = MealPlanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Mostrar planes del usuario y planes públicos (sin usuario)
        return MealPlan.objects.filter(
            Q(user=self.request.user) | Q(user__isnull=True)
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def custom(self, request):
        """Obtener solo planes personalizados del usuario"""
        plans = MealPlan.objects.filter(user=request.user, is_custom=True)
        serializer = self.get_serializer(plans, many=True)
        return Response(serializer.data)


class NutritionEntryViewSet(viewsets.ModelViewSet):
    """ViewSet para entradas de seguimiento nutricional"""
    serializer_class = NutritionEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NutritionEntry.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def by_date(self, request):
        """Obtener entrada por fecha"""
        date_str = request.query_params.get('date', str(date.today()))
        try:
            entry = NutritionEntry.objects.get(user=request.user, date=date_str)
            serializer = self.get_serializer(entry)
            return Response(serializer.data)
        except NutritionEntry.DoesNotExist:
            return Response({'detail': 'No encontrado'}, status=status.HTTP_404_NOT_FOUND)


class ExerciseRoutineViewSet(viewsets.ModelViewSet):
    """ViewSet para rutinas de ejercicio"""
    serializer_class = ExerciseRoutineSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Mostrar rutinas del usuario y rutinas públicas (sin usuario)
        return ExerciseRoutine.objects.filter(
            Q(user=self.request.user) | Q(user__isnull=True)
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def custom(self, request):
        """Obtener solo rutinas personalizadas del usuario"""
        routines = ExerciseRoutine.objects.filter(user=request.user, is_custom=True)
        serializer = self.get_serializer(routines, many=True)
        return Response(serializer.data)


class ExerciseEntryViewSet(viewsets.ModelViewSet):
    """ViewSet para entradas de seguimiento de ejercicio"""
    serializer_class = ExerciseEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ExerciseEntry.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def by_date(self, request):
        """Obtener entrada por fecha"""
        date_str = request.query_params.get('date', str(date.today()))
        try:
            entry = ExerciseEntry.objects.get(user=request.user, date=date_str)
            serializer = self.get_serializer(entry)
            return Response(serializer.data)
        except ExerciseEntry.DoesNotExist:
            return Response({'detail': 'No encontrado'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def weekly_stats(self, request):
        """Obtener estadísticas semanales"""
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_entries = ExerciseEntry.objects.filter(
            user=request.user,
            date__gte=week_start,
            date__lte=today
        )
        
        total_workouts = week_entries.count()
        total_minutes = sum(entry.duration for entry in week_entries)
        average_minutes = total_minutes / total_workouts if total_workouts > 0 else 0
        
        return Response({
            'total_workouts': total_workouts,
            'total_minutes': total_minutes,
            'average_minutes': round(average_minutes),
            'days_completed': total_workouts
        })


class MoodEntryViewSet(viewsets.ModelViewSet):
    """ViewSet para entradas de ánimo"""
    serializer_class = MoodEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MoodEntry.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        try:
            serializer.save(user=self.request.user)
            if __debug__:
                print(f"[MoodEntry] Created entry for user {self.request.user.id}, date {serializer.validated_data.get('date')}, mood {serializer.validated_data.get('mood')}")
        except Exception as e:
            print(f"[MoodEntry] Error creating entry: {e}")
            raise

    def perform_update(self, serializer):
        # Asegurar que solo el usuario propietario pueda actualizar
        try:
            instance = serializer.instance
            if __debug__:
                print(f"[MoodEntry] Updating entry {instance.id} for user {self.request.user.id}, date {serializer.validated_data.get('date')}, mood {serializer.validated_data.get('mood')}")
            serializer.save(user=self.request.user)
            if __debug__:
                print(f"[MoodEntry] Successfully updated entry {instance.id}")
        except Exception as e:
            print(f"[MoodEntry] Error updating entry: {e}")
            raise

    @action(detail=False, methods=['get'])
    def by_date(self, request):
        """Obtener entrada por fecha"""
        date_str = request.query_params.get('date', str(date.today()))
        try:
            entry = MoodEntry.objects.get(user=request.user, date=date_str)
            serializer = self.get_serializer(entry)
            return Response(serializer.data)
        except MoodEntry.DoesNotExist:
            return Response({'detail': 'No encontrado'}, status=status.HTTP_404_NOT_FOUND)


class AISessionViewSet(viewsets.ModelViewSet):
    """ViewSet para sesiones de IA"""
    serializer_class = AISessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AISession.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def by_date(self, request):
        """Obtener sesión por fecha"""
        date_str = request.query_params.get('date', str(date.today()))
        try:
            session = AISession.objects.filter(user=request.user, date=date_str).first()
            if session:
                serializer = self.get_serializer(session)
                return Response(serializer.data)
            return Response({'detail': 'No encontrado'}, status=status.HTTP_404_NOT_FOUND)
        except:
            return Response({'detail': 'Error'}, status=status.HTTP_400_BAD_REQUEST)


class HydrationEntryViewSet(viewsets.ModelViewSet):
    """ViewSet para entradas de hidratación"""
    serializer_class = HydrationEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Siempre filtrar por el usuario autenticado para seguridad"""
        return HydrationEntry.objects.filter(user=self.request.user).order_by('-date')

    def perform_create(self, serializer):
        """Asegurar que el usuario se asigne automáticamente"""
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        """Asegurar que solo se actualicen registros del usuario autenticado"""
        serializer.save()

    def get_object(self):
        """Obtener objeto asegurando que pertenezca al usuario"""
        obj = super().get_object()
        # Verificación adicional de seguridad
        if obj.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("No tienes permiso para acceder a este registro.")
        return obj

    def create(self, request, *args, **kwargs):
        """Crear o actualizar (upsert) un registro de hidratación para user+date.

        Si ya existe un registro para la fecha proporcionada, lo actualiza y devuelve 200.
        Si no existe, crea uno nuevo y devuelve 201.
        """
        date_str = request.data.get('date')
        if not date_str:
            return Response(
                {'success': False, 'detail': 'El campo "date" es requerido (YYYY-MM-DD).'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar formato de fecha
        try:
            from datetime import datetime
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return Response(
                {'success': False, 'detail': 'Formato de fecha inválido. Use YYYY-MM-DD.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar que amount y goal sean números positivos
        amount = request.data.get('amount')
        goal = request.data.get('goal')
        
        if amount is not None:
            try:
                amount = float(amount)
                if amount < 0:
                    return Response(
                        {'success': False, 'detail': 'El campo "amount" debe ser mayor o igual a 0.'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except (ValueError, TypeError):
                return Response(
                    {'success': False, 'detail': 'El campo "amount" debe ser un número válido.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

        if goal is not None:
            try:
                goal = float(goal)
                if goal <= 0:
                    return Response(
                        {'success': False, 'detail': 'El campo "goal" debe ser mayor que 0.'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except (ValueError, TypeError):
                return Response(
                    {'success': False, 'detail': 'El campo "goal" debe ser un número válido.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

        try:
            # Buscar registro existente solo para el usuario autenticado
            existing = HydrationEntry.objects.get(user=request.user, date=date_str)
            # Actualizar registro existente
            serializer = self.get_serializer(existing, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except HydrationEntry.DoesNotExist:
            # Crear nuevo registro
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user)
            headers = self.get_success_headers(serializer.data)
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            return Response(
                {'success': False, 'detail': f'Error al guardar: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def update(self, request, *args, **kwargs):
        """Actualizar registro asegurando que pertenezca al usuario"""
        partial = kwargs.pop('partial', True)  # Por defecto usar PATCH (partial=True)
        instance = self.get_object()
        
        # Validar datos si se proporcionan
        amount = request.data.get('amount')
        goal = request.data.get('goal')
        date_str = request.data.get('date')
        
        # Validar formato de fecha si se proporciona
        if date_str:
            try:
                from datetime import datetime
                datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                return Response(
                    {'success': False, 'detail': 'Formato de fecha inválido. Use YYYY-MM-DD.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if amount is not None:
            try:
                amount = float(amount)
                if amount < 0:
                    return Response(
                        {'success': False, 'detail': 'El campo "amount" debe ser mayor o igual a 0.'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except (ValueError, TypeError):
                return Response(
                    {'success': False, 'detail': 'El campo "amount" debe ser un número válido.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

        if goal is not None:
            try:
                goal = float(goal)
                if goal <= 0:
                    return Response(
                        {'success': False, 'detail': 'El campo "goal" debe ser mayor que 0.'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except (ValueError, TypeError):
                return Response(
                    {'success': False, 'detail': 'El campo "goal" debe ser un número válido.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

        try:
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'success': False, 'detail': f'Error al actualizar: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    def list(self, request, *args, **kwargs):
        """Listar todas las entradas del usuario autenticado"""
        response = super().list(request, *args, **kwargs)
        return Response({
            'success': True,
            'data': response.data
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def by_date(self, request):
        """Obtener entrada por fecha para el usuario autenticado"""
        date_str = request.query_params.get('date', str(date.today()))
        
        # Validar formato de fecha
        try:
            from datetime import datetime
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return Response(
                {'success': False, 'detail': 'Formato de fecha inválido. Use YYYY-MM-DD.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Buscar solo en registros del usuario autenticado
            entry = HydrationEntry.objects.get(user=request.user, date=date_str)
            serializer = self.get_serializer(entry)
            return Response({
                'success': True,
                'data': serializer.data
            })
        except HydrationEntry.DoesNotExist:
            return Response({
                'success': False,
                'data': None,
                'detail': 'No encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response(
                {'success': False, 'detail': f'Error al obtener: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        except Exception as e:
            return Response(
                {'success': False, 'detail': f'Error al obtener: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GratitudeEntryViewSet(viewsets.ModelViewSet):
    """ViewSet para entradas del diario de gratitud"""
    serializer_class = GratitudeEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return GratitudeEntry.objects.filter(user=self.request.user).order_by('-date', '-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
class AIChatMessageViewSet(viewsets.ModelViewSet):
    """ViewSet para mensajes de chat con IA"""
    serializer_class = AIChatMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = AIChatMessage.objects.filter(user=self.request.user)
        chat_type = self.request.query_params.get('chat_type', None)
        session_id = self.request.query_params.get('session_id', None)
        
        if chat_type:
            queryset = queryset.filter(chat_type=chat_type)
        if session_id:
            queryset = queryset.filter(session_id=session_id)
        
        return queryset.order_by('timestamp')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def sessions(self, request):
        """Obtener lista de sesiones de chat agrupadas"""
        chat_type = request.query_params.get('chat_type', None)
        if not chat_type:
            return Response({'detail': 'chat_type es requerido'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener todas las sesiones únicas del usuario para este tipo de chat
        sessions = AIChatMessage.objects.filter(
            user=request.user,
            chat_type=chat_type
        ).values('session_id').distinct().order_by('-timestamp')
        
        # Para cada sesión, obtener el primer y último mensaje
        sessions_list = []
        for session in sessions:
            if session['session_id']:
                messages = AIChatMessage.objects.filter(
                    user=request.user,
                    chat_type=chat_type,
                    session_id=session['session_id']
                ).order_by('timestamp')
                
                if messages.exists():
                    first_msg = messages.first()
                    last_msg = messages.last()
                    sessions_list.append({
                        'session_id': session['session_id'],
                        'date': first_msg.timestamp.date().isoformat(),
                        'preview': last_msg.text[:100],
                        'message_count': messages.count(),
                    })
        
        return Response(sessions_list)


# ============================================
# VIEWSETS DE COMUNIDAD
# ============================================

class PostViewSet(viewsets.ModelViewSet):
    """ViewSet para posts de la comunidad"""
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Post.objects.filter(is_deleted=False)
        
        # Filtrar por categoría si se proporciona
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        
        # Filtrar por usuario si se proporciona
        user_id = self.request.query_params.get('user', None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filtrar por dominio si se proporciona (Psicología, Nutrición, Ejercicio)
        domain = self.request.query_params.get('domain', None)
        if domain:
            queryset = queryset.filter(domain=domain)
        
        return queryset.order_by('-created_at')

    def create(self, request, *args, **kwargs):
        """Sobrescribir create para asegurar que se retorne el objeto correctamente"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        
        if __debug__:
            print(f"[Post] Created post {serializer.instance.id}, returning data")
        
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def perform_create(self, serializer):
        post = serializer.save(user=self.request.user)
        # Actualizar contadores
        post.likes_count = post.likes.count()
        post.comments_count = post.comments.filter(is_deleted=False).count()
        post.save()
        # Actualizar logros de comunidad (posts compartidos)
        update_achievements(self.request.user, 'community', progress_increment=1)
        if __debug__:
            print(f"[Post] Created post {post.id} for user {self.request.user.id}, category: {post.category}, content: {post.content[:50]}")
    
    def get_serializer_context(self):
        """Asegurar que el contexto incluya el request"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_update(self, serializer):
        # Solo el propietario puede actualizar
        if serializer.instance.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("No tienes permiso para editar este post")
        serializer.save()

    def perform_destroy(self, instance):
        # Soft delete
        instance.is_deleted = True
        instance.save()

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Dar like o quitar like a un post"""
        post = self.get_object()
        like, created = PostLike.objects.get_or_create(
            post=post,
            user=request.user
        )
        
        if not created:
            # Si ya existe, quitar el like
            like.delete()
            is_liked = False
            # Eliminar notificación si existe
            Notification.objects.filter(
                user=post.user,
                notification_type='post_like',
                post=post,
                from_user=request.user
            ).delete()
        else:
            is_liked = True
            # Crear notificación solo si no es el mismo usuario
            if post.user != request.user:
                notification = Notification.objects.create(
                    user=post.user,
                    notification_type='post_like',
                    title='Nueva reacción',
                    message=f'{request.user.username} reaccionó a tu publicación',
                    post=post,
                    from_user=request.user
                )
                # Enviar notificación en tiempo real
                send_notification_realtime(notification)
        
        # Actualizar contador
        post.likes_count = post.likes.count()
        post.save()
        
        return Response({
            'is_liked': is_liked,
            'likes_count': post.likes_count
        })

    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        """Obtener todos los comentarios de un post"""
        post = self.get_object()
        comments = post.comments.filter(is_deleted=False).order_by('created_at')
        serializer = CommentSerializer(comments, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post', 'delete'])
    def save(self, request, pk=None):
        """Guardar o desguardar un post"""
        try:
            post = self.get_object()
            
            if request.method == 'POST':
                # Guardar post
                saved_post, created = SavedPost.objects.get_or_create(
                    user=request.user,
                    post=post
                )
                print(f"[Post] User {request.user.id} saved post {post.id}, created: {created}")
                
                # Verificar que se guardó en la BD
                exists = SavedPost.objects.filter(user=request.user, post=post).exists()
                print(f"[Post] Verification - SavedPost exists in DB: {exists}")
                
                if created:
                    return Response({
                        'success': True, 
                        'data': {'saved': True, 'post_id': post.id},
                        'message': 'Post guardado'
                    }, status=status.HTTP_201_CREATED)
                else:
                    return Response({
                        'success': True,
                        'data': {'saved': True, 'post_id': post.id},
                        'message': 'Post ya estaba guardado'
                    })
            else:
                # Desguardar post
                deleted_count = SavedPost.objects.filter(user=request.user, post=post).delete()[0]
                print(f"[Post] User {request.user.id} unsaved post {post.id}, deleted: {deleted_count}")
                if deleted_count > 0:
                    return Response({
                        'success': True,
                        'data': {'saved': False, 'post_id': post.id},
                        'message': 'Post desguardado'
                    })
                else:
                    return Response({
                        'success': False,
                        'data': {'saved': False, 'post_id': post.id},
                        'message': 'Post no estaba guardado'
                    }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"[Post] Error in save action: {e}")
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def report(self, request, pk=None):
        """Reportar un post"""
        post = self.get_object()
        reason = request.data.get('reason')
        description = request.data.get('description', '')
        
        if not reason:
            return Response({
                'success': False,
                'error': 'Se requiere una razón para el reporte'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar si el usuario ya reportó este post
        existing_report = PostReport.objects.filter(
            post=post,
            reported_by=request.user,
            status='pending'
        ).first()
        
        if existing_report:
            return Response({
                'success': False,
                'message': 'Ya has reportado este post anteriormente'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Crear reporte
        report = PostReport.objects.create(
            post=post,
            reported_by=request.user,
            reason=reason,
            description=description
        )
        
        serializer = PostReportSerializer(report)
        return Response({
            'success': True,
            'message': 'Post reportado. Será revisado por un administrador.',
            'report': serializer.data
        }, status=status.HTTP_201_CREATED)


class CommentViewSet(viewsets.ModelViewSet):
    """ViewSet para comentarios"""
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Comment.objects.filter(is_deleted=False)
        
        # Filtrar por post si se proporciona
        post_id = self.request.query_params.get('post', None)
        if post_id:
            queryset = queryset.filter(post_id=post_id)
        
        return queryset.order_by('created_at')

    def perform_create(self, serializer):
        comment = serializer.save(user=self.request.user)
        # Actualizar contador del post
        post = comment.post
        post.comments_count = post.comments.filter(is_deleted=False).count()
        post.save()
        # Actualizar logros de comunidad (comentarios realizados)
        update_achievements(self.request.user, 'community', progress_increment=1)
        # Actualizar contador del comentario
        comment.likes_count = comment.likes.count()
        comment.save()
        
        # Crear notificación solo si no es el mismo usuario que creó el post
        if post.user != self.request.user:
            notification = Notification.objects.create(
                user=post.user,
                notification_type='post_comment',
                title='Nuevo comentario',
                message=f'{self.request.user.username} comentó en tu publicación',
                post=post,
                comment=comment,
                from_user=self.request.user
            )
            # Enviar notificación en tiempo real
            send_notification_realtime(notification)

    def perform_update(self, serializer):
        # Solo el propietario puede actualizar
        if serializer.instance.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("No tienes permiso para editar este comentario")
        serializer.save()

    def perform_destroy(self, instance):
        # Soft delete
        instance.is_deleted = True
        instance.save()
        # Actualizar contador del post
        post = instance.post
        post.comments_count = post.comments.filter(is_deleted=False).count()
        post.save()

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Dar like o quitar like a un comentario"""
        comment = self.get_object()
        like, created = CommentLike.objects.get_or_create(
            comment=comment,
            user=request.user
        )
        
        if not created:
            # Si ya existe, quitar el like
            like.delete()
            is_liked = False
        else:
            is_liked = True
        
        # Actualizar contador
        comment.likes_count = comment.likes.count()
        comment.save()
        
        return Response({
            'is_liked': is_liked,
            'likes_count': comment.likes_count
        })


class AchievementViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para logros (solo lectura)"""
    serializer_class = AchievementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Achievement.objects.filter(is_active=True).order_by('achievement_type', 'requirement')


class UserAchievementViewSet(viewsets.ModelViewSet):
    """ViewSet para logros de usuarios"""
    serializer_class = UserAchievementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Permitir filtrar por usuario (para ver logros de otros)
        user_id = self.request.query_params.get('user', None)
        if user_id:
            try:
                target_user = User.objects.get(id=user_id)
                queryset = UserAchievement.objects.filter(user=target_user)
            except User.DoesNotExist:
                return UserAchievement.objects.none()
        else:
            queryset = UserAchievement.objects.filter(user=self.request.user)
        
        # Filtrar por completados si se proporciona
        completed = self.request.query_params.get('completed', None)
        if completed == 'true':
            queryset = queryset.filter(is_completed=True)
        elif completed == 'false':
            queryset = queryset.filter(is_completed=False)
        
        return queryset.order_by('-completed_at', '-created_at')

    def create(self, request, *args, **kwargs):
        """Crear logro o desbloquear usando slug del frontend"""
        achievement_id = request.data.get('achievement_id')
        user = request.user

        if not achievement_id:
            return Response({'error': 'achievement_id es requerido'}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Definir Mapa de Slugs a Nombres (Backend Names)
        # Esto debe coincidir con constants/gamification.ts
        SLUG_TO_NAME = {
            'first_workout': 'Primer Paso',
            'streak_week': 'Semana de Fuego',
            'streak_4_weeks': 'Disciplina de Hierro', 
            'discipline_total': 'Disciplina Total',
            'no_pain_no_gain': 'No Pain, No Gain',
            'lobo_solitario': 'Lobo Solitario',
            # Achievements de Nutrición
            'nutrition_streak_7': 'Racha Nutricional', # Ejemplo
            'water_champion': 'Campeón de Hidratación' 
        }

        achievement = None

        # 2. Intentar buscar por ID numérico (Comportamiento standard)
        if isinstance(achievement_id, int) or (isinstance(achievement_id, str) and achievement_id.isdigit()):
            try:
                achievement = Achievement.objects.get(id=int(achievement_id))
            except Achievement.DoesNotExist:
                pass
        
        # 3. Si no, intentar buscar por Slug
        if not achievement and isinstance(achievement_id, str):
            target_name = SLUG_TO_NAME.get(achievement_id)
            if target_name:
                achievement = Achievement.objects.filter(name=target_name).first()
            
            # Si no está en el mapa, intentar buscar por nombre directo (fallback)
            if not achievement:
                 achievement = Achievement.objects.filter(name__iexact=achievement_id).first()

        if not achievement:
            return Response({'error': 'Logro no encontrado o ID inválido'}, status=status.HTTP_404_NOT_FOUND)

        # 4. Desbloquear Logro
        user_achievement, created = UserAchievement.objects.get_or_create(
            user=user,
            achievement=achievement
        )

        if not user_achievement.is_completed:
            user_achievement.is_completed = True
            user_achievement.completed_at = timezone.now()
            user_achievement.progress = achievement.requirement # Maximizar progreso
            user_achievement.save()

            # Crear notificación
            Notification.objects.create(
                user=user,
                notification_type='achievement',
                title='¡Logro Desbloqueado!',
                message=f'Has desbloqueado: {achievement.name}',
                achievement=achievement
            )
            
            serializer = self.get_serializer(user_achievement)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response({'message': 'Logro ya desbloqueado previamente'}, status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def progress(self, request):
        """Obtener progreso de logros del usuario"""
        user_id = request.query_params.get('user', None)
        if user_id:
             # Si se especifica un usuario, usar ese
            try:
                target_user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                 return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        else:
            # Si no, usar el usuario autenticado
            target_user = request.user

        user_achievements = UserAchievement.objects.filter(user=target_user)
        achievements = Achievement.objects.filter(is_active=True)
        
        progress_data = []
        for achievement in achievements:
            user_achievement = user_achievements.filter(achievement=achievement).first()
            progress_data.append({
                'achievement': AchievementSerializer(achievement).data,
                'progress': user_achievement.progress if user_achievement else 0,
                'is_completed': user_achievement.is_completed if user_achievement else False,
                'completed_at': user_achievement.completed_at if user_achievement else None,
            })
        
        return Response(progress_data)


class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet para notificaciones"""
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Solo las notificaciones del usuario autenticado"""
        queryset = Notification.objects.filter(user=self.request.user)
        
        # Filtrar por leídas/no leídas si se proporciona
        is_read = self.request.query_params.get('is_read', None)
        if is_read is not None:
            is_read_bool = is_read.lower() == 'true'
            queryset = queryset.filter(is_read=is_read_bool)
        
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        """Las notificaciones solo se crean automáticamente, no manualmente"""
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("No puedes crear notificaciones manualmente")

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Marcar una notificación como leída"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'success': True, 'is_read': True})

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Marcar todas las notificaciones como leídas"""
        count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True)
        return Response({'success': True, 'marked_count': count})

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Obtener el número de notificaciones no leídas"""
        count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        return Response({'count': count})


class SavedPostViewSet(viewsets.ModelViewSet):
    """ViewSet para publicaciones guardadas"""
    serializer_class = SavedPostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = SavedPost.objects.filter(user=self.request.user).select_related('post', 'post__user', 'post__user__profile').order_by('-created_at')
        print(f"[SavedPost] Loading saved posts for user {self.request.user.id}, count: {queryset.count()}")
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        print(f"[SavedPost] Created saved post for user {self.request.user.id}")

    def get_serializer_context(self):
        """Asegurar que el contexto incluya el request"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def list(self, request, *args, **kwargs):
        """Listar publicaciones guardadas con el post completo"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        print(f"[SavedPost] Returning {len(serializer.data)} saved posts")
        return Response({
            'success': True,
            'data': serializer.data
        })


class PostReportViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para reportes de publicaciones (solo lectura para usuarios, admin puede editar)"""
    serializer_class = PostReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Los usuarios solo pueden ver sus propios reportes
        # Los administradores pueden ver todos
        if self.request.user.is_staff:
            return PostReport.objects.all().order_by('-created_at')
        return PostReport.objects.filter(reported_by=self.request.user).order_by('-created_at')


class UserFollowViewSet(viewsets.ModelViewSet):
    """ViewSet para seguir/dejar de seguir usuarios"""
    serializer_class = UserFollowSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Por defecto, mostrar a quién sigue el usuario actual
        return UserFollow.objects.filter(follower=self.request.user).order_by('-created_at')

    @action(detail=False, methods=['post'], url_path='follow/(?P<user_id>[^/.]+)')
    def follow(self, request, user_id=None):
        """Seguir a un usuario"""
        try:
            user_to_follow = User.objects.get(id=user_id)
            
            # No se puede seguir a uno mismo
            if user_to_follow == request.user:
                return Response({
                    'success': False,
                    'error': 'No puedes seguirte a ti mismo'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Verificar si ya lo sigue
            follow, created = UserFollow.objects.get_or_create(
                follower=request.user,
                following=user_to_follow
            )
            
            if created:
                # Crear notificación para el usuario que está siendo seguido
                notification = Notification.objects.create(
                    user=user_to_follow,
                    notification_type='user_follow',
                    title='Nuevo Seguidor',
                    message=f'{request.user.username} comenzó a seguirte',
                    from_user=request.user
                )
                
                # Enviar notificación en tiempo real
                send_notification_realtime(notification)
                
                print(f"[UserFollow] User {request.user.id} started following {user_to_follow.id}, notification sent")
                
                return Response({
                    'success': True,
                    'data': UserFollowSerializer(follow, context={'request': request}).data,
                    'message': f'Ahora sigues a {user_to_follow.username}'
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': True,
                    'data': UserFollowSerializer(follow, context={'request': request}).data,
                    'message': 'Ya sigues a este usuario'
                })
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Usuario no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['delete'], url_path='unfollow/(?P<user_id>[^/.]+)')
    def unfollow(self, request, user_id=None):
        """Dejar de seguir a un usuario"""
        try:
            user_to_unfollow = User.objects.get(id=user_id)
            deleted_count = UserFollow.objects.filter(
                follower=request.user,
                following=user_to_unfollow
            ).delete()[0]
            
            if deleted_count > 0:
                return Response({
                    'success': True,
                    'message': f'Ya no sigues a {user_to_unfollow.username}'
                })
            else:
                return Response({
                    'success': False,
                    'error': 'No estabas siguiendo a este usuario'
                }, status=status.HTTP_404_NOT_FOUND)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Usuario no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'], url_path='followers')
    def followers(self, request):
        """Obtener lista de seguidores del usuario actual"""
        followers = UserFollow.objects.filter(following=request.user).order_by('-created_at')
        serializer = self.get_serializer(followers, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })

    @action(detail=False, methods=['get'], url_path='following')
    def following(self, request):
        """Obtener lista de usuarios que sigue el usuario actual"""
        following = UserFollow.objects.filter(follower=request.user).order_by('-created_at')
        serializer = self.get_serializer(following, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })


class ConversationViewSet(viewsets.ModelViewSet):
    """ViewSet para conversaciones entre usuarios"""
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Mostrar conversaciones donde el usuario es user1 o user2
        # Incluir todas las conversaciones, incluso las pendientes con mensajes
        return Conversation.objects.filter(
            Q(user1=self.request.user) | Q(user2=self.request.user)
        ).order_by('-last_message_at', '-created_at')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def list(self, request, *args, **kwargs):
        """Listar conversaciones con estructura correcta"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        if __debug__:
            print(f"[Conversation] Returning {len(serializer.data)} conversations for user {request.user.id}")
        return Response({
            'success': True,
            'data': serializer.data
        })

    @action(detail=False, methods=['post'], url_path='create')
    def create_conversation(self, request):
        """Crear una nueva conversación (invitación)"""
        user2_id = request.data.get('user2')
        if not user2_id:
            return Response({
                'success': False,
                'error': 'user2 es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Convertir a int si viene como string
        try:
            user2_id = int(user2_id)
        except (ValueError, TypeError):
            return Response({
                'success': False,
                'error': 'user2 debe ser un número válido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user2 = User.objects.get(id=user2_id)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Usuario no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Verificar que no se puede crear conversación consigo mismo
        if user2 == request.user:
            return Response({
                'success': False,
                'error': 'No puedes crear una conversación contigo mismo'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar que ambos usuarios se siguen mutuamente
        follows1 = UserFollow.objects.filter(follower=request.user, following=user2).exists()
        follows2 = UserFollow.objects.filter(follower=user2, following=request.user).exists()
        
        if not (follows1 and follows2):
            return Response({
                'success': False,
                'error': 'Ambos usuarios deben seguirse mutuamente para iniciar una conversación'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar si ya existe una conversación
        conversation = Conversation.objects.filter(
            Q(user1=request.user, user2=user2) | Q(user1=user2, user2=request.user)
        ).first()
        
        if conversation:
            # Si ya existe y está rechazada, cambiar estado a pendiente
            if conversation.status == 'rejected':
                conversation.status = 'pending'
                conversation.initiated_by = request.user
                conversation.save()
                serializer = self.get_serializer(conversation)
                return Response({
                    'success': True,
                    'data': serializer.data,
                    'message': 'Invitación enviada nuevamente'
                })
            else:
                serializer = self.get_serializer(conversation)
                return Response({
                    'success': True,
                    'data': serializer.data,
                    'message': 'La conversación ya existe'
                })
        
        # Crear nueva conversación
        user1, user2_sorted = sorted([request.user, user2], key=lambda u: u.id)
        conversation = Conversation.objects.create(
            user1=user1,
            user2=user2_sorted,
            status='pending',
            initiated_by=request.user
        )
        
        # Crear notificación para el usuario que recibe la invitación
        notification = Notification.objects.create(
            user=user2,
            notification_type='conversation_request',
            title='Nueva Invitación de Chat',
            message=f'{request.user.username} quiere iniciar una conversación contigo',
            from_user=request.user
        )
        send_notification_realtime(notification)
        
        serializer = self.get_serializer(conversation)
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Invitación enviada'
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='accept')
    def accept(self, request, pk=None):
        """Aceptar una invitación de conversación"""
        conversation = self.get_object()
        
        # Verificar que el usuario actual es el destinatario
        if conversation.get_other_user(request.user) != conversation.initiated_by:
            return Response({
                'success': False,
                'error': 'No tienes permiso para aceptar esta conversación'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if conversation.status != 'pending':
            return Response({
                'success': False,
                'error': 'Esta conversación ya fue procesada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        conversation.status = 'accepted'
        conversation.save()
        
        # Crear notificación para el iniciador
        notification = Notification.objects.create(
            user=conversation.initiated_by,
            notification_type='conversation_accepted',
            title='Invitación Aceptada',
            message=f'{request.user.username} aceptó tu invitación de chat',
            from_user=request.user
        )
        send_notification_realtime(notification)
        
        serializer = self.get_serializer(conversation)
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Invitación aceptada'
        })

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        """Rechazar una invitación de conversación"""
        conversation = self.get_object()
        
        # Verificar que el usuario actual es el destinatario
        if conversation.get_other_user(request.user) != conversation.initiated_by:
            return Response({
                'success': False,
                'error': 'No tienes permiso para rechazar esta conversación'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if conversation.status != 'pending':
            return Response({
                'success': False,
                'error': 'Esta conversación ya fue procesada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        conversation.status = 'rejected'
        conversation.save()
        
        serializer = self.get_serializer(conversation)
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Invitación rechazada'
        })

    @action(detail=False, methods=['get'], url_path='pending')
    def pending(self, request):
        """Obtener invitaciones pendientes"""
        pending_conversations = Conversation.objects.filter(
            Q(user1=request.user) | Q(user2=request.user),
            status='pending'
        ).exclude(initiated_by=request.user).order_by('-created_at')
        
        serializer = self.get_serializer(pending_conversations, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })


class DirectMessageViewSet(viewsets.ModelViewSet):
    """ViewSet para mensajes directos entre usuarios"""
    serializer_class = DirectMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        conversation_id = self.request.query_params.get('conversation')
        if conversation_id:
            # Verificar que el usuario es parte de la conversación
            # Permitir cargar mensajes de conversaciones aceptadas o pendientes con mensajes
            conversation = Conversation.objects.filter(
                Q(user1=self.request.user) | Q(user2=self.request.user),
                id=conversation_id
            ).first()
            if conversation:
                # Si la conversación está pendiente pero tiene mensajes, aceptarla automáticamente
                if conversation.status == 'pending' and DirectMessage.objects.filter(conversation=conversation).exists():
                    conversation.status = 'accepted'
                    conversation.save()
                return DirectMessage.objects.filter(conversation=conversation).order_by('-created_at')
        return DirectMessage.objects.none()

    def list(self, request, *args, **kwargs):
        """Listar mensajes de una conversación con estructura correcta"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        if __debug__:
            print(f"[DirectMessage] Returning {len(serializer.data)} messages for conversation")
        return Response({
            'success': True,
            'data': serializer.data
        })

    def create(self, request, *args, **kwargs):
        """Sobrescribir create para devolver la estructura correcta"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        conversation = serializer.validated_data['conversation']
        
        # Verificar que el usuario es parte de la conversación
        if conversation.user1 != self.request.user and conversation.user2 != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("No eres parte de esta conversación")
        
        # Si la conversación está pendiente, aceptarla automáticamente cuando se envía el primer mensaje
        if conversation.status == 'pending':
            conversation.status = 'accepted'
            conversation.save()
            
            # Crear notificación para el otro usuario de que la conversación fue aceptada
            other_user = conversation.get_other_user(self.request.user)
            notification = Notification.objects.create(
                user=other_user,
                notification_type='conversation_accepted',
                title='Conversación Aceptada',
                message=f'{self.request.user.username} inició una conversación contigo',
                from_user=self.request.user
            )
            send_notification_realtime(notification)
        
        message = serializer.save(sender=self.request.user)
        
        # Actualizar last_message_at de la conversación
        conversation.last_message_at = timezone.now()
        conversation.save()
        
        # Crear o actualizar notificación para el otro usuario
        other_user = conversation.get_other_user(self.request.user)
        
        # Buscar si ya existe una notificación no leída de chat del mismo usuario
        existing_notification = Notification.objects.filter(
            user=other_user,
            notification_type='chat_message',
            from_user=self.request.user,
            is_read=False
        ).order_by('-created_at').first()
        
        if existing_notification:
            # Actualizar notificación existente
            # Contar mensajes no leídos de esta conversación enviados por el remitente
            # (mensajes que el otro usuario aún no ha leído)
            unread_count = DirectMessage.objects.filter(
                conversation=conversation,
                sender=self.request.user,
                is_read=False
            ).count()
            
            if unread_count > 1:
                existing_notification.message = f'{unread_count} mensajes nuevos de {self.request.user.username}'
            else:
                existing_notification.message = f'{self.request.user.username} te envió un mensaje'
            
            # Actualizar timestamp para mantenerla arriba en la lista
            existing_notification.created_at = timezone.now()
            existing_notification.save()
            notification = existing_notification
        else:
            # Crear nueva notificación
            notification = Notification.objects.create(
                user=other_user,
                notification_type='chat_message',
                title='Nuevo Mensaje',
                message=f'{self.request.user.username} te envió un mensaje',
                from_user=self.request.user
            )
        
        send_notification_realtime(notification)
        
        # Enviar mensaje en tiempo real vía WebSocket
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        if channel_layer:
            message_data = DirectMessageSerializer(message, context={'request': self.request}).data
            # Enviar al grupo de notificaciones del usuario (que también maneja mensajes directos)
            async_to_sync(channel_layer.group_send)(
                f'notifications_{other_user.id}',
                {
                    'type': 'direct_message',
                    'message': message_data
                }
            )
        
        print(f"[DirectMessage] Message {message.id} sent from {self.request.user.id} to {other_user.id}")

    @action(detail=True, methods=['post'], url_path='mark_read')
    def mark_read(self, request, pk=None):
        """Marcar un mensaje como leído"""
        message = self.get_object()
        
        # Solo el destinatario puede marcar como leído
        if message.sender == request.user:
            return Response({
                'success': False,
                'error': 'No puedes marcar tus propios mensajes como leídos'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        conversation = message.conversation
        if conversation.user1 != request.user and conversation.user2 != request.user:
            return Response({
                'success': False,
                'error': 'No eres parte de esta conversación'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if not message.is_read:
            message.is_read = True
            message.read_at = timezone.now()
            message.save()
        
        return Response({
            'success': True,
            'data': DirectMessageSerializer(message, context={'request': request}).data
        })

    @action(detail=False, methods=['post'], url_path='mark_conversation_read')
    def mark_conversation_read(self, request):
        """Marcar todos los mensajes de una conversación como leídos"""
        conversation_id = request.data.get('conversation_id')
        if not conversation_id:
            return Response({
                'success': False,
                'error': 'conversation_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            conversation = Conversation.objects.filter(
                Q(user1=request.user) | Q(user2=request.user),
                id=conversation_id
            ).first()
            
            if not conversation:
                return Response({
                    'success': False,
                    'error': 'Conversación no encontrada'
                }, status=status.HTTP_404_NOT_FOUND)
        except Conversation.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Conversación no encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Marcar todos los mensajes no leídos del otro usuario como leídos
        updated = DirectMessage.objects.filter(
            conversation=conversation,
            is_read=False
        ).exclude(sender=request.user).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        # Marcar notificaciones de chat de esta conversación como leídas
        other_user = conversation.get_other_user(request.user)
        Notification.objects.filter(
            user=request.user,
            notification_type='chat_message',
            from_user=other_user,
            is_read=False
        ).update(is_read=True)
        
        return Response({
            'success': True,
            'marked_count': updated
        })
