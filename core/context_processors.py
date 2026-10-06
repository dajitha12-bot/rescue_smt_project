from django.utils import timezone
from gdacs_integration.services import get_latest_sync_status
from notifications_app.models import Notification

def rescuegrid_global_context(request):
    unread_count = 0
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()

    gdacs_status = get_latest_sync_status()

    return {
        'APP_NAME': 'RESCUEGRID',
        'APP_TAGLINE': 'Multi-Region Emergency Response & Relief Platform for India',
        'CURRENT_TIME': timezone.now(),
        'UNREAD_NOTIFICATIONS_COUNT': unread_count,
        'GDACS_SUMMARY': gdacs_status,
        'PRIMARY_COLOR': '#FE8D01',
        'SECONDARY_COLOR': '#FFA53F',
    }
