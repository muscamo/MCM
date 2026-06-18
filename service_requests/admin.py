from django.contrib import admin
from .models import Department, ServiceType, ServiceRequest, Assignment, RequestComment, RequestAttachment


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at', 'updated_at']
    search_fields = ['name', 'description']


@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'requires_team_assignment', 'created_at']
    search_fields = ['name', 'description']


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ['title', 'service_type', 'department', 'status', 'priority', 'created_at']
    list_filter = ['status', 'priority', 'service_type', 'department', 'created_at']
    search_fields = ['title', 'description', 'requester__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['request', 'assigned_to', 'assigned_at', 'is_primary']
    list_filter = ['is_primary', 'assigned_at']
    search_fields = ['request__title', 'assigned_to__username']


@admin.register(RequestComment)
class RequestCommentAdmin(admin.ModelAdmin):
    list_display = ['request', 'author', 'is_internal', 'created_at']
    list_filter = ['is_internal', 'created_at']
    search_fields = ['comment', 'author__username']


@admin.register(RequestAttachment)
class RequestAttachmentAdmin(admin.ModelAdmin):
    list_display = ['filename', 'request', 'uploaded_by', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['filename', 'request__title']
