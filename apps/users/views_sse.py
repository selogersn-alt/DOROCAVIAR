import time
import json
from django.http import StreamingHttpResponse
from django.contrib.auth.decorators import login_required
from .models import Notification, PrivateMessage

def sse_event_generator(user):
    last_checked_notif_id = None
    last_checked_msg_id = None
    
    # Chargement initial des notifications non lues
    unread_notifs = Notification.objects.filter(recipient=user, is_read=False)
    unread_msgs = PrivateMessage.objects.filter(recipient=user, is_read=False)
    
    notif_count = unread_notifs.count()
    msg_count = unread_msgs.count()
    
    last_notif = unread_notifs.first()
    last_msg = unread_msgs.first()
    
    last_checked_notif_id = last_notif.id if last_notif else None
    last_checked_msg_id = last_msg.id if last_msg else None
    
    initial_data = {
        'type': 'INIT',
        'notifications_count': notif_count,
        'messages_count': msg_count,
    }
    yield f"event: message\ndata: {json.dumps(initial_data)}\n\n"
    
    while True:
        # Non-blocking pause pour limiter la charge
        time.sleep(2)
        
        try:
            current_unread_notifs = Notification.objects.filter(recipient=user, is_read=False)
            current_unread_msgs = PrivateMessage.objects.filter(recipient=user, is_read=False)
            
            c_notif_count = current_unread_notifs.count()
            c_msg_count = current_unread_msgs.count()
            
            c_last_notif = current_unread_notifs.first()
            c_last_msg = current_unread_msgs.first()
            
            c_notif_id = c_last_notif.id if c_last_notif else None
            c_msg_id = c_last_msg.id if c_last_msg else None
            
            triggered = False
            data = {'type': 'UPDATE'}
            
            if c_notif_id != last_checked_notif_id or c_notif_count != notif_count:
                triggered = True
                data['notification'] = {
                    'text': c_last_notif.text if c_last_notif else "",
                    'type': c_last_notif.notification_type if c_last_notif else "SYSTEM",
                    'sender': c_last_notif.sender.username if c_last_notif and c_last_notif.sender else "Système",
                    'link': c_last_notif.link if c_last_notif else ""
                }
                last_checked_notif_id = c_notif_id
                notif_count = c_notif_count
                
            if c_msg_id != last_checked_msg_id or c_msg_count != msg_count:
                triggered = True
                data['message'] = {
                    'sender': c_last_msg.sender.username if c_last_msg else "",
                    'content': c_last_msg.content if c_last_msg else "",
                    'image': c_last_msg.image.url if c_last_msg and c_last_msg.image else ""
                }
                last_checked_msg_id = c_msg_id
                msg_count = c_msg_count
                
            if triggered:
                data['notifications_count'] = notif_count
                data['messages_count'] = msg_count
                yield f"event: message\ndata: {json.dumps(data)}\n\n"
                
        except Exception:
            # Sortie propre en cas d'erreur de connexion
            break

@login_required
def sse_notifications_stream(request):
    """Flux SSE temps réel pour les notifications et messages privés."""
    response = StreamingHttpResponse(sse_event_generator(request.user), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'  # Empêche Nginx de mettre en tampon le flux
    return response
