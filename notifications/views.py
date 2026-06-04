from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import Notification


@login_required
def notification_list(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    return render(request, 'notifications/notification_list.html', {'notifications': notifications})


@login_required
def mark_as_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.is_read = True
    notification.save()
    
    if request.headers.get('HX-Request'):
        from django.template.loader import render_to_string
        unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        
        # Return updated notification item
        context = {'notification': notification}
        response_html = render_to_string('notifications/notification_item.html', context, request=request)
        
        # Add badge HTML to response headers
        if unread_count > 0:
            badge_html = f'<span class="badge bg-danger" id="notification-badge">{unread_count}</span>'
        else:
            badge_html = ''
        
        from django.http import HttpResponse
        response_obj = HttpResponse(response_html)
        response_obj['X-Badge-Update'] = badge_html
        return response_obj
    
    if notification.request:
        return redirect('request_detail', pk=notification.request.pk)
    return redirect('notification_list')


@login_required
def mark_all_as_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    
    if request.headers.get('HX-Request'):
        from django.template.loader import render_to_string
        notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
        context = {'notifications': notifications}
        response_html = render_to_string('notifications/notification_list_partial.html', context, request=request)
        
        # Add badge HTML to response headers
        badge_html = ''
        
        from django.http import HttpResponse
        response_obj = HttpResponse(response_html)
        response_obj['X-Badge-Update'] = badge_html
        return response_obj
    
    return redirect('notification_list')
