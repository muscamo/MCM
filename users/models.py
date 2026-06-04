from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('department_staff', 'Department Staff'),
        ('departmental_director', 'Departmental Director'),
        ('communication_director', 'Communication Director'),
        ('media_team', 'Media Team'),
        ('admin', 'Admin'),
    ]

    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='department_staff')
    departments = models.ManyToManyField(
        'requests.Department',
        blank=True,
        related_name='members'
    )
    phone = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Google OAuth fields (commented out until django-allauth is installed)
    # google_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    # google_picture_url = models.URLField(blank=True, null=True)
    # google_verified_email = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

    def is_department_staff(self):
        return self.role in ['department_staff', 'departmental_director']

    def is_departmental_director(self):
        return self.role == 'departmental_director'

    def is_communication_director(self):
        return self.role == 'communication_director'

    def is_media_team(self):
        return self.role == 'media_team'

    def is_admin(self):
        return self.role == 'admin' or self.is_superuser

    class Meta:
        ordering = ['username']
