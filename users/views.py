from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.db.models import Q
from .forms import UserRegistrationForm, UserUpdateForm
from .models import User


class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    redirect_authenticated_user = True


class CustomLogoutView(LogoutView):
    next_page = 'login'


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to the Media Center.')
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'users/register.html', {'form': form})


@login_required
def profile(request):
    is_admin = request.user.is_superuser or request.user.is_admin()
    
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user, is_admin=is_admin)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserUpdateForm(instance=request.user, is_admin=is_admin)
    
    return render(request, 'users/profile.html', {'form': form})


def is_admin(user):
    return user.is_superuser or user.is_communication_director() or user.is_admin()

def is_superuser(user):
    return user.is_superuser or user.is_admin()


@login_required
@user_passes_test(is_superuser)
def user_list(request):
    users = User.objects.all()
    
    # Filter by role if provided
    role_filter = request.GET.get('role')
    if role_filter:
        users = users.filter(role=role_filter)
    
    # Filter by department if provided
    dept_filter = request.GET.get('department')
    if dept_filter:
        users = users.filter(department_id=dept_filter)
    
    # Search if provided
    search_query = request.GET.get('search')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    context = {
        'users': users,
        'role_filter': role_filter,
        'dept_filter': dept_filter,
        'search_query': search_query,
    }
    return render(request, 'users/user_list.html', context)


@login_required
@user_passes_test(is_superuser)
def user_create(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User {user.username} created successfully!')
            return redirect('user_list')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'users/user_form.html', {'form': form, 'title': 'Create User'})


@login_required
@user_passes_test(is_superuser)
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=user, is_admin=True)
        if form.is_valid():
            form.save()
            messages.success(request, f'User {user.username} updated successfully!')
            return redirect('user_list')
    else:
        form = UserUpdateForm(instance=user, is_admin=True)
    
    return render(request, 'users/user_form.html', {'form': form, 'title': 'Edit User', 'user': user})


@login_required
@user_passes_test(is_superuser)
def user_toggle_active(request, pk):
    user = get_object_or_404(User, pk=pk)
    
    # Prevent deactivating yourself
    if user == request.user:
        messages.error(request, 'You cannot deactivate yourself.')
        return redirect('user_list')
    
    user.is_active = not user.is_active
    user.save()
    
    status = 'activated' if user.is_active else 'deactivated'
    messages.success(request, f'User {user.username} has been {status}.')
    
    return redirect('user_list')
