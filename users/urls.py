from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('manage/', views.user_list, name='user_list'),
    path('manage/create/', views.user_create, name='user_create'),
    path('manage/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('manage/<int:pk>/toggle-active/', views.user_toggle_active, name='user_toggle_active'),
]
