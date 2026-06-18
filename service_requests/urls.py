from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('requests/', views.request_list, name='request_list'),
    path('requests/create/', views.request_create, name='request_create'),
    path('requests/<int:pk>/', views.request_detail, name='request_detail'),
    path('requests/<int:pk>/approve/', views.request_approve, name='request_approve'),
    path('requests/<int:pk>/assign/', views.request_assign, name='request_assign'),
    path('requests/<int:pk>/progress/', views.progress_update, name='progress_update'),
    path('requests/<int:pk>/comment/', views.add_comment, name='add_comment'),
    path('requests/<int:pk>/attachment/', views.add_attachment, name='add_attachment'),
    path('assignments/<int:pk>/reassign/', views.reassign_assignment, name='reassign_assignment'),
    path('departments/', views.department_list, name='department_list'),
    path('departments/create/', views.department_create, name='department_create'),
    path('departments/<int:pk>/edit/', views.department_edit, name='department_edit'),
    path('service-types/', views.service_type_list, name='service_type_list'),
    path('service-types/create/', views.service_type_create, name='service_type_create'),
    path('service-types/<int:pk>/edit/', views.service_type_edit, name='service_type_edit'),
    path('service-types/<int:pk>/toggle/', views.service_type_toggle_active, name='service_type_toggle_active'),
]
