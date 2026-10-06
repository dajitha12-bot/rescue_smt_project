from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Notification

@login_required
def notifications_list(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')

    filter_type = request.GET.get('type')
    if filter_type:
        notifications = notifications.filter(notification_type=filter_type)

    return render(request, 'notifications/list.html', {
        'notifications': notifications,
        'filter_type': filter_type,
    })

@login_required
def mark_notification_read(request, notification_id):
    notif = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notif.is_read = True
    notif.save()
    if notif.link_url:
        return redirect(notif.link_url)
    return redirect('notifications_list')

@login_required
def mark_all_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect('notifications_list')
