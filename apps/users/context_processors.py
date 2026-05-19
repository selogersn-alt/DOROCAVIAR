from .models import FriendRequest, PrivateMessage, Notification

def notifications_context(request):
    if request.user.is_authenticated:
        unread_messages = PrivateMessage.objects.filter(recipient=request.user, is_read=False).count()
        pending_requests = FriendRequest.objects.filter(receiver=request.user, status='PENDING').count()
        unread_notifications = Notification.objects.filter(recipient=request.user, is_read=False).count()
        
        return {
            'unread_messages_count': unread_messages,
            'pending_requests_count': pending_requests,
            'unread_notifications_count': unread_notifications,
            'total_notifications': unread_messages + pending_requests + unread_notifications
        }
    return {}
