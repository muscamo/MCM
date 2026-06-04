from django.db import models
from django.contrib.auth import get_user_model
from requests.models import ServiceRequest

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
