from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class Department(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class ServiceType(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    requires_team_assignment = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True, help_text='Whether this service type is available for new requests')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class ServiceRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    title = models.CharField(max_length=300)
    description = models.TextField()
    service_type = models.ForeignKey(ServiceType, on_delete=models.PROTECT, related_name='requests')
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='requests')
    requester = models.ForeignKey(User, on_delete=models.PROTECT, related_name='submitted_requests')
    
    # Date and time information
    event_date = models.DateField(help_text='Date of the event/program')
    event_time = models.TimeField(help_text='Time of the event/program', blank=True, null=True)
    deadline = models.DateField(help_text='Deadline for completion', blank=True, null=True)
    
    # Status and priority
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Approval
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_requests')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Progress tracking
    progress_percentage = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Progress percentage (0-100)'
    )
    progress_notes = models.TextField(blank=True, help_text='Notes on progress')
    
    # Additional details
    location = models.CharField(max_length=300, blank=True, help_text='Location of the event')
    expected_attendees = models.IntegerField(blank=True, null=True, help_text='Expected number of attendees')
    special_requirements = models.TextField(blank=True, help_text='Any special requirements')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.service_type.name}"

    class Meta:
        ordering = ['-created_at']


class Assignment(models.Model):
    request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name='assignments')
    assigned_to = models.ForeignKey(User, on_delete=models.PROTECT, related_name='assignments')
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='made_assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, help_text='Notes for the assigned team member')
    is_primary = models.BooleanField(default=False, help_text='Primary assignee for this request')

    def __str__(self):
        return f"{self.request.title} -> {self.assigned_to.get_full_name()}"

    class Meta:
        unique_together = ['request', 'assigned_to']
        ordering = ['-assigned_at']


class RequestComment(models.Model):
    request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.PROTECT, related_name='request_comments')
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_internal = models.BooleanField(default=False, help_text='Internal comment (only visible to media team)')

    def __str__(self):
        return f"Comment by {self.author.get_full_name()} on {self.request.title}"

    class Meta:
        ordering = ['-created_at']


class RequestAttachment(models.Model):
    request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='request_attachments/%Y/%m/')
    filename = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='uploaded_attachments')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.filename} - {self.request.title}"

    class Meta:
        ordering = ['-uploaded_at']
