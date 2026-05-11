import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from .models import Notification

User = get_user_model()


class NotificationConsumer(AsyncWebsocketConsumer):
    """Consumer para notificaciones en tiempo real"""
    
    async def connect(self):
        # Obtener el token de los query params
        query_string = self.scope.get('query_string', b'').decode()
        token = None
        
        # Parsear query string para obtener el token
        if query_string:
            params = dict(param.split('=') for param in query_string.split('&') if '=' in param)
            token = params.get('token', None)
        
        if not token:
            await self.close()
            return
        
        # Verificar el token y obtener el usuario
        user = await self.get_user_from_token(token)
        if not user:
            await self.close()
            return
        
        # Guardar el usuario en el scope
        self.user = user
        self.room_group_name = f'notifications_{user.id}'
        
        # Unirse al grupo de notificaciones del usuario
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        print(f"[WebSocket] Usuario {user.id} conectado a notificaciones")
    
    async def disconnect(self, close_code):
        # Salir del grupo
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        print(f"[WebSocket] Usuario desconectado")
    
    async def receive(self, text_data):
        """Recibir mensajes del cliente"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                # Responder con pong para mantener la conexión viva
                await self.send(text_data=json.dumps({
                    'type': 'pong'
                }))
        except json.JSONDecodeError:
            pass
    
    async def notification_created(self, event):
        """Enviar notificación al cliente cuando se crea una nueva"""
        notification_data = event['notification']
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': notification_data
        }))
        if __debug__:
            print(f"[WebSocket] Notificación enviada a cliente: {notification_data.get('id')}")
    
    async def notification_updated(self, event):
        """Enviar actualización de notificación al cliente"""
        notification_data = event['notification']
        await self.send(text_data=json.dumps({
            'type': 'notification_update',
            'notification': notification_data
        }))
    
    async def unread_count_update(self, event):
        """Enviar actualización del contador de no leídas"""
        count = event['count']
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': count
        }))
    
    async def direct_message(self, event):
        """Enviar mensaje directo al cliente"""
        message_data = event['message']
        await self.send(text_data=json.dumps({
            'type': 'direct_message',
            'message': message_data
        }))
        if __debug__:
            print(f"[WebSocket] Mensaje directo enviado a cliente: {message_data.get('id')}")
    
    @database_sync_to_async
    def get_user_from_token(self, token):
        """Obtener usuario desde el token"""
        try:
            token_obj = Token.objects.get(key=token)
            return token_obj.user
        except Token.DoesNotExist:
            return None

