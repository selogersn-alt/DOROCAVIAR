import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Notification, PrivateMessage

@login_required
def sse_notifications_stream(request):
    """
    Flux d'information haute performance et non-bloquant pour les notifications et messages.
    Remplace l'ancienne implémentation SSE qui bloquait les processus Gunicorn.
    """
    user = request.user
    
    # 1. Récupération des counts non lus
    unread_notifs = Notification.objects.filter(recipient=user, is_read=False)
    unread_msgs = PrivateMessage.objects.filter(recipient=user, is_read=False)
    
    notif_count = unread_notifs.count()
    msg_count = unread_msgs.count()
    
    last_notif = unread_notifs.first()
    last_msg = unread_msgs.first()
    
    current_notif_id = last_notif.id if last_notif else None
    current_msg_id = last_msg.id if last_msg else None
    
    # 2. Récupération des identifiants précédemment connus du client
    client_notif_id = request.GET.get('last_notif_id')
    client_msg_id = request.GET.get('last_msg_id')
    
    has_update = False
    notification_data = None
    message_data = None
    
    # Validation du premier chargement ou de la présence de nouveautés
    if client_notif_id is not None:
        try:
            client_notif_id = int(client_notif_id) if client_notif_id else None
        except ValueError:
            client_notif_id = None
            
        if current_notif_id and current_notif_id != client_notif_id:
            has_update = True
            notification_data = {
                'text': last_notif.text,
                'type': last_notif.notification_type,
                'sender': last_notif.sender.username if last_notif.sender else "Système",
                'link': last_notif.link or ""
            }
            
    if client_msg_id is not None:
        try:
            client_msg_id = int(client_msg_id) if client_msg_id else None
        except ValueError:
            client_msg_id = None
            
        if current_msg_id and current_msg_id != client_msg_id:
            has_update = True
            message_data = {
                'sender': last_msg.sender.username,
                'content': last_msg.content,
                'image': last_msg.image.url if last_msg.image else ""
            }
            
    return JsonResponse({
        'status': 'success',
        'notifications_count': notif_count,
        'messages_count': msg_count,
        'last_notif_id': current_notif_id,
        'last_msg_id': current_msg_id,
        'has_update': has_update,
        'notification': notification_data,
        'message': message_data
    })
