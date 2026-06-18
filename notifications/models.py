from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from service_requests.models import ServiceRequest

User = get_user_model()


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('request_submitted', 'Request Submitted'),
        ('request_approved', 'Request Approved'),
        ('request_assigned', 'Request Assigned'),
        ('request_rejected', 'Request Rejected'),
        ('progress_updated', 'Progress Updated'),
        ('comment_added', 'Comment Added'),
        ('request_completed', 'Request Completed'),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.recipient.get_full_name()}"

    class Meta:
        ordering = ['-created_at']


@receiver(post_save, sender=Notification)
def send_notification_email(sender, instance, created, **kwargs):
    if created and instance.recipient.email:
        subject = instance.title
        from_email = settings.DEFAULT_FROM_EMAIL

        # Get the site URL from settings or use a default
        site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')

        # Render the email template
        html_message = render_to_string(
            'notifications/email_notification.html',
            {'notification': instance, 'site_url': site_url}
        )

        # Send the email
        send_mail(
            subject=subject,
            message=instance.message,
            from_email=from_email,
            recipient_list=[instance.recipient.email],
            html_message=html_message,
            fail_silently=False
        )
