from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from .models import ServiceRequest, ServiceType, Department, Assignment, RequestComment, RequestAttachment
from .forms import (
    ServiceRequestForm, ServiceRequestApprovalForm, AssignmentForm,
    ProgressUpdateForm, RequestCommentForm, RequestAttachmentForm,
    DepartmentForm, ServiceTypeForm, ReassignForm
)
from notifications.models import Notification
from users.models import User


def is_admin(user):
    return user.is_superuser or user.is_communication_director() or user.is_admin()

def is_superuser(user):
    return user.is_superuser or user.is_admin()


@login_required
def dashboard(request):
    user = request.user
    
    if user.is_communication_director() or user.is_admin():
        # Communication director and admin see all pending requests
        pending_requests = ServiceRequest.objects.filter(status='pending')
        assigned_requests = ServiceRequest.objects.filter(status__in=['approved', 'assigned', 'in_progress'])
        context = {
            'pending_requests': pending_requests[:5],
            'assigned_requests': assigned_requests[:5],
            'total_pending': pending_requests.count(),
            'total_assigned': assigned_requests.count(),
        }
    elif user.is_media_team():
        # Media team sees their assigned requests
        assignments = Assignment.objects.filter(assigned_to=user)
        my_requests = [a.request for a in assignments]
        in_progress = [r for r in my_requests if r.status == 'in_progress']
        context = {
            'my_requests': my_requests[:5],
            'in_progress': in_progress[:5],
            'total_assigned': len(my_requests),
        }
    else:
        # Department staff and departmental director see their own requests
        my_requests = ServiceRequest.objects.filter(requester=user)
        pending = my_requests.filter(status='pending')
        in_progress = my_requests.filter(status='in_progress')
        completed = my_requests.filter(status='completed')
        context = {
            'my_requests': my_requests[:5],
            'pending': pending[:5],
            'in_progress': in_progress[:5],
            'completed': completed[:5],
            'total_requests': my_requests.count(),
        }
    
    # Get unread notifications
    unread_notifications = Notification.objects.filter(recipient=user, is_read=False)[:5]
    context['unread_notifications'] = unread_notifications
    
    return render(request, 'requests/dashboard.html', context)


@login_required
def request_list(request):
    user = request.user
    
    if user.is_communication_director() or user.is_admin():
        requests = ServiceRequest.objects.all()
    elif user.is_media_team():
        assignments = Assignment.objects.filter(assigned_to=user)
        requests = [a.request for a in assignments]
    else:
        requests = ServiceRequest.objects.filter(requester=user)
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        requests = requests.filter(status=status_filter)
    
    context = {'requests': requests, 'status_filter': status_filter}
    return render(request, 'requests/request_list.html', context)


@login_required
def request_create(request):
    if request.method == 'POST':
        form = ServiceRequestForm(request.POST, user=request.user)
        if form.is_valid():
            service_request = form.save(commit=False)
            service_request.requester = request.user
            service_request.save()
            
            # Create notification for communication director
            directors = request.user.__class__.objects.filter(role='communication_director')
            for director in directors:
                Notification.objects.create(
                    recipient=director,
                    notification_type='request_submitted',
                    title=f'New Service Request: {service_request.title}',
                    message=f'{request.user.get_full_name()} has submitted a new request for {service_request.service_type.name}.',
                    request=service_request
                )
            
            # Send email notification
            try:
                send_mail(
                    subject=f'New Service Request: {service_request.title}',
                    message=f'A new service request has been submitted by {request.user.get_full_name()}.\n\nTitle: {service_request.title}\nService Type: {service_request.service_type.name}\nDepartment: {service_request.department.name}\n\nPlease review and approve the request.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[director.email for director in directors if director.email],
                    fail_silently=True,
                )
            except:
                pass
            
            messages.success(request, 'Service request submitted successfully!')
            return redirect('request_detail', pk=service_request.pk)
    else:
        form = ServiceRequestForm(user=request.user)
    
    return render(request, 'requests/request_form.html', {'form': form})


@login_required
def request_detail(request, pk):
    service_request = get_object_or_404(ServiceRequest, pk=pk)
    assignments = service_request.assignments.all()
    comments = service_request.comments.filter(is_internal=False)
    internal_comments = service_request.comments.filter(is_internal=True)
    attachments = service_request.attachments.all()
    
    comment_form = RequestCommentForm()
    attachment_form = RequestAttachmentForm()
    
    context = {
        'request': service_request,
        'assignments': assignments,
        'comments': comments,
        'internal_comments': internal_comments,
        'attachments': attachments,
        'comment_form': comment_form,
        'attachment_form': attachment_form,
    }
    return render(request, 'requests/request_detail.html', context)


@login_required
def request_approve(request, pk):
    if not (request.user.is_communication_director() or request.user.is_admin()):
        messages.error(request, 'You do not have permission to approve requests.')
        return redirect('request_detail', pk=pk)
    
    service_request = get_object_or_404(ServiceRequest, pk=pk)
    
    if request.method == 'POST':
        form = ServiceRequestApprovalForm(request.POST)
        form.fields['assign_to'].queryset = User.objects.filter(role='media_team')
        if form.is_valid():
            action = form.cleaned_data['action']
            assign_to = form.cleaned_data.get('assign_to', [])
            assign_to_all = form.cleaned_data.get('assign_to_all', False)
            
            if action == 'approve':
                service_request.status = 'approved'
                service_request.approved_by = request.user
                service_request.approved_at = timezone.now()
                service_request.save()
                
                # Handle assignments
                if assign_to_all:
                    # Assign to all media team members
                    media_team = User.objects.filter(role='media_team')
                    for i, member in enumerate(media_team):
                        Assignment.objects.create(
                            request=service_request,
                            assigned_to=member,
                            is_primary=(i == 0)
                        )
                        # Notify each member
                        Notification.objects.create(
                            recipient=member,
                            notification_type='assignment',
                            title=f'New Assignment: {service_request.title}',
                            message=f'{request.user.get_full_name()} assigned this task to you.',
                            request=service_request
                        )
                        # Send email notification
                        try:
                            send_mail(
                                subject=f'New Assignment: {service_request.title}',
                                message=f'You have been assigned to a new task: {service_request.title}',
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                recipient_list=[member.email],
                                fail_silently=True,
                            )
                        except:
                            pass
                elif assign_to:
                    # Assign to selected team members
                    for i, member in enumerate(assign_to):
                        Assignment.objects.create(
                            request=service_request,
                            assigned_to=member,
                            is_primary=(i == 0)
                        )
                        # Notify each member
                        Notification.objects.create(
                            recipient=member,
                            notification_type='assignment',
                            title=f'New Assignment: {service_request.title}',
                            message=f'{request.user.get_full_name()} assigned this task to you.',
                            request=service_request
                        )
                        # Send email notification
                        try:
                            send_mail(
                                subject=f'New Assignment: {service_request.title}',
                                message=f'You have been assigned to a new task: {service_request.title}',
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                recipient_list=[member.email],
                                fail_silently=True,
                            )
                        except:
                            pass
                
                # Update request status if assignments were made
                if assign_to_all or assign_to:
                    service_request.status = 'assigned'
                    service_request.save()
                
                # Notify requester
                Notification.objects.create(
                    recipient=service_request.requester,
                    notification_type='request_approved',
                    title=f'Request Approved: {service_request.title}',
                    message=f'Your service request has been approved by {request.user.get_full_name()} and assigned to the media team.',
                    request=service_request
                )
                
                # Send email
                try:
                    send_mail(
                        subject=f'Request Approved: {service_request.title}',
                        message=f'Your service request has been approved by {request.user.get_full_name()} and assigned to the media team.',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[service_request.requester.email],
                        fail_silently=True,
                    )
                except:
                    pass
                
                messages.success(request, 'Request approved and assigned successfully!')
            else:
                rejection_reason = form.cleaned_data.get('rejection_reason')
                if not rejection_reason:
                    messages.error(request, 'Please provide a reason for rejection.')
                    return redirect('request_detail', pk=pk)
                
                service_request.status = 'rejected'
                service_request.rejection_reason = rejection_reason
                service_request.save()
                
                # Notify requester
                Notification.objects.create(
                    recipient=service_request.requester,
                    notification_type='request_rejected',
                    title=f'Request Rejected: {service_request.title}',
                    message=f'Your service request has been rejected.\n\nReason: {rejection_reason}',
                    request=service_request
                )
                
                # Send email
                try:
                    send_mail(
                        subject=f'Request Rejected: {service_request.title}',
                        message=f'Your service request has been rejected by {request.user.get_full_name()}.\n\nReason: {rejection_reason}',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[service_request.requester.email],
                        fail_silently=True,
                    )
                except:
                    pass
                
                messages.success(request, 'Request rejected successfully!')
            
            return redirect('request_detail', pk=pk)
    
    form = ServiceRequestApprovalForm()
    form.fields['assign_to'].queryset = User.objects.filter(role='media_team')
    return render(request, 'requests/request_approve.html', {'form': form, 'request': service_request})


@login_required
def request_assign(request, pk):
    if not (request.user.is_communication_director() or request.user.is_admin()):
        messages.error(request, 'You do not have permission to assign requests.')
        return redirect('request_detail', pk=pk)
    
    service_request = get_object_or_404(ServiceRequest, pk=pk)
    
    if service_request.status != 'approved':
        messages.error(request, 'Request must be approved before assigning.')
        return redirect('request_detail', pk=pk)
    
    if request.method == 'POST':
        form = AssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.request = service_request
            assignment.assigned_by = request.user
            assignment.save()
            
            # Update request status
            service_request.status = 'assigned'
            service_request.save()
            
            # Notify assigned team member
            Notification.objects.create(
                recipient=assignment.assigned_to,
                notification_type='request_assigned',
                title=f'New Assignment: {service_request.title}',
                message=f'You have been assigned to this service request. Please review the details and start working on it.',
                request=service_request
            )
            
            # Notify requester
            Notification.objects.create(
                recipient=service_request.requester,
                notification_type='request_assigned',
                title=f'Request Assigned: {service_request.title}',
                message=f'Your request has been assigned to {assignment.assigned_to.get_full_name()}.',
                request=service_request
            )
            
            # Send emails
            try:
                send_mail(
                    subject=f'New Assignment: {service_request.title}',
                    message=f'You have been assigned to a new service request.\n\nTitle: {service_request.title}\nService Type: {service_request.service_type.name}\n\nPlease review the details and start working on it.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[assignment.assigned_to.email],
                    fail_silently=True,
                )
                
                send_mail(
                    subject=f'Request Assigned: {service_request.title}',
                    message=f'Your request has been assigned to {assignment.assigned_to.get_full_name()}.\n\nTitle: {service_request.title}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[service_request.requester.email],
                    fail_silently=True,
                )
            except:
                pass
            
            messages.success(request, 'Team member assigned successfully!')
            return redirect('request_detail', pk=pk)
    else:
        form = AssignmentForm()
    
    # Get media team members
    media_team = request.user.__class__.objects.filter(role='media_team')
    
    context = {
        'form': form,
        'request': service_request,
        'media_team': media_team,
    }
    return render(request, 'requests/request_assign.html', context)


@login_required
def progress_update(request, pk):
    service_request = get_object_or_404(ServiceRequest, pk=pk)
    
    # Check if user is assigned to this request or is a communication director
    is_assigned = Assignment.objects.filter(request=service_request, assigned_to=request.user).exists()
    if not (is_assigned or request.user.is_communication_director()):
        messages.error(request, 'You do not have permission to update progress on this request.')
        return redirect('request_detail', pk=pk)
    
    if request.method == 'POST':
        form = ProgressUpdateForm(request.POST)
        if form.is_valid():
            progress = form.cleaned_data['progress_percentage']
            notes = form.cleaned_data.get('progress_notes', '')
            
            service_request.progress_percentage = progress
            if notes:
                service_request.progress_notes = notes
            service_request.save()
            
            # Update status based on progress
            if progress == 100:
                service_request.status = 'completed'
                service_request.save()
                
                # Notify requester
                Notification.objects.create(
                    recipient=service_request.requester,
                    notification_type='request_completed',
                    title=f'Request Completed: {service_request.title}',
                    message=f'Your service request has been completed.',
                    request=service_request
                )
                
                # Send email
                try:
                    send_mail(
                        subject=f'Request Completed: {service_request.title}',
                        message=f'Your service request has been completed.\n\nTitle: {service_request.title}',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[service_request.requester.email],
                        fail_silently=True,
                    )
                except:
                    pass
            elif progress > 0 and service_request.status == 'assigned':
                service_request.status = 'in_progress'
                service_request.save()
            
            # Notify requester of progress update
            Notification.objects.create(
                recipient=service_request.requester,
                notification_type='progress_updated',
                title=f'Progress Updated: {service_request.title}',
                message=f'Progress on your request has been updated to {progress}%.',
                request=service_request
            )
            
            messages.success(request, 'Progress updated successfully!')
            
            if request.headers.get('HX-Request'):
                return HttpResponse(status=204)
            return redirect('request_detail', pk=pk)
    else:
        form = ProgressUpdateForm(initial={'progress_percentage': service_request.progress_percentage})
    
    return render(request, 'requests/progress_update.html', {'form': form, 'request': service_request})


@login_required
def add_comment(request, pk):
    service_request = get_object_or_404(ServiceRequest, pk=pk)
    
    if request.method == 'POST':
        form = RequestCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.request = service_request
            comment.author = request.user
            
            # Only media team and communication directors can add internal comments
            if form.cleaned_data.get('is_internal') and not (request.user.is_media_team() or request.user.is_communication_director()):
                comment.is_internal = False
            
            comment.save()
            
            # Notify relevant users
            if comment.is_internal:
                # Notify media team members and communication director
                assignments = service_request.assignments.all()
                recipients = [a.assigned_to for a in assignments]
                directors = request.user.__class__.objects.filter(role='communication_director')
                recipients.extend(directors)
            else:
                # Notify requester and assigned team members
                recipients = [service_request.requester]
                assignments = service_request.assignments.all()
                recipients.extend([a.assigned_to for a in assignments])
            
            for recipient in recipients:
                if recipient != request.user:
                    Notification.objects.create(
                        recipient=recipient,
                        notification_type='comment_added',
                        title=f'New Comment: {service_request.title}',
                        message=f'{request.user.get_full_name()} added a comment.',
                        request=service_request
                    )
            
            messages.success(request, 'Comment added successfully!')
            
            if request.headers.get('HX-Request'):
                return render(request, 'requests/comment_list.html', {
                    'request': service_request,
                    'comments': service_request.comments.filter(is_internal=comment.is_internal),
                })
            return redirect('request_detail', pk=pk)
    
    return redirect('request_detail', pk=pk)


@login_required
def add_attachment(request, pk):
    service_request = get_object_or_404(ServiceRequest, pk=pk)
    
    if request.method == 'POST':
        form = RequestAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.request = service_request
            attachment.uploaded_by = request.user
            attachment.filename = request.FILES['file'].name
            attachment.save()
            
            messages.success(request, 'Attachment added successfully!')
            
            if request.headers.get('HX-Request'):
                return render(request, 'requests/attachment_list.html', {
                    'request': service_request,
                    'attachments': service_request.attachments.all(),
                })
            return redirect('request_detail', pk=pk)
    
    return redirect('request_detail', pk=pk)


@login_required
@user_passes_test(is_admin)
def department_list(request):
    departments = Department.objects.all()
    return render(request, 'requests/department_list.html', {'departments': departments})


@login_required
@user_passes_test(is_admin)
def department_create(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            department = form.save()
            messages.success(request, f'Department {department.name} created successfully!')
            return redirect('department_list')
    else:
        form = DepartmentForm()
    
    return render(request, 'requests/department_form.html', {'form': form, 'title': 'Create Department'})


@login_required
@user_passes_test(is_admin)
def department_edit(request, pk):
    department = get_object_or_404(Department, pk=pk)
    
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, f'Department {department.name} updated successfully!')
            return redirect('department_list')
    else:
        form = DepartmentForm(instance=department)
    
    # Handle adding a member
    if request.method == 'POST' and 'add_member' in request.POST:
        user_id = request.POST.get('user_id')
        if user_id:
            user = get_object_or_404(User, pk=user_id)
            department.members.add(user)
            messages.success(request, f'{user.get_full_name()} added to {department.name} successfully!')
            return redirect('department_edit', pk=pk)
    
    # Handle removing a member
    if request.method == 'POST' and 'remove_member' in request.POST:
        user_id = request.POST.get('user_id')
        if user_id:
            user = get_object_or_404(User, pk=user_id)
            department.members.remove(user)
            messages.success(request, f'{user.get_full_name()} removed from {department.name} successfully!')
            return redirect('department_edit', pk=pk)
    
    # Get non-members for the add member dropdown
    non_members = User.objects.exclude(departments=department)
    
    context = {
        'form': form,
        'title': 'Edit Department',
        'department': department,
        'members': department.members.all(),
        'non_members': non_members,
    }
    return render(request, 'requests/department_form.html', context)


@login_required
@user_passes_test(is_admin)
def service_type_list(request):
    service_types = ServiceType.objects.all()
    return render(request, 'requests/service_type_list.html', {'service_types': service_types})


@login_required
@user_passes_test(is_admin)
def service_type_create(request):
    if request.method == 'POST':
        form = ServiceTypeForm(request.POST)
        if form.is_valid():
            service_type = form.save()
            messages.success(request, f'Service type {service_type.name} created successfully!')
            return redirect('service_type_list')
    else:
        form = ServiceTypeForm()
    
    return render(request, 'requests/service_type_form.html', {'form': form, 'title': 'Create Service Type'})


@login_required
@user_passes_test(is_admin)
def service_type_edit(request, pk):
    service_type = get_object_or_404(ServiceType, pk=pk)
    
    if request.method == 'POST':
        form = ServiceTypeForm(request.POST, instance=service_type)
        if form.is_valid():
            form.save()
            messages.success(request, f'Service type {service_type.name} updated successfully!')
            return redirect('service_type_list')
    else:
        form = ServiceTypeForm(instance=service_type)
    
    return render(request, 'requests/service_type_form.html', {'form': form, 'title': 'Edit Service Type', 'service_type': service_type})


@login_required
@user_passes_test(is_admin)
def service_type_toggle_active(request, pk):
    service_type = get_object_or_404(ServiceType, pk=pk)
    service_type.is_active = not service_type.is_active
    service_type.save()
    
    if service_type.is_active:
        messages.success(request, f'Service type {service_type.name} has been activated.')
    else:
        messages.success(request, f'Service type {service_type.name} has been suspended.')
    
    return redirect('service_type_list')


@login_required
def reassign_assignment(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    service_request = assignment.request
    
    # Only communication director or admin can reassign
    if not (request.user.is_communication_director() or request.user.is_admin()):
        messages.error(request, 'You do not have permission to reassign this task.')
        return redirect('request_detail', pk=service_request.pk)
    
    if request.method == 'POST':
        form = ReassignForm(request.POST)
        form.fields['assigned_to'].queryset = User.objects.filter(role='media_team').exclude(pk=assignment.assigned_to.pk)
        if form.is_valid():
            new_assignee = form.cleaned_data['assigned_to']
            notes = form.cleaned_data.get('notes', '')
            
            # Check if new assignee already has an assignment for this request
            existing_assignment = Assignment.objects.filter(request=service_request, assigned_to=new_assignee).first()
            
            if existing_assignment:
                # Update existing assignment
                existing_assignment.is_primary = True
                existing_assignment.notes = notes
                existing_assignment.save()
                
                # Mark old assignment as not primary
                assignment.is_primary = False
                assignment.save()
            else:
                # Create new assignment
                new_assignment = Assignment.objects.create(
                    request=service_request,
                    assigned_to=new_assignee,
                    notes=notes,
                    is_primary=True
                )
                
                # Mark old assignment as not primary
                assignment.is_primary = False
                assignment.save()
            
            # Update request status
            service_request.status = 'assigned'
            service_request.save()
            
            # Notify new assignee
            Notification.objects.create(
                recipient=new_assignee,
                notification_type='assignment',
                title=f'New Assignment: {service_request.title}',
                message=f'{request.user.get_full_name()} reassigned this task to you.',
                request=service_request
            )
            
            # Notify old assignee
            if assignment.assigned_to != request.user:
                Notification.objects.create(
                    recipient=assignment.assigned_to,
                    notification_type='assignment',
                    title=f'Task Reassigned: {service_request.title}',
                    message=f'{request.user.get_full_name()} reassigned this task to {new_assignee.get_full_name()}.',
                    request=service_request
                )
            
            # Send email notification
            try:
                send_mail(
                    subject=f'Task Reassigned: {service_request.title}',
                    message=f'You have been assigned to a new task: {service_request.title}\n\nNotes: {notes}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[new_assignee.email],
                    fail_silently=True,
                )
            except:
                pass
            
            messages.success(request, f'Task reassigned to {new_assignee.get_full_name()} successfully!')
            return redirect('request_detail', pk=service_request.pk)
    else:
        form = ReassignForm()
        form.fields['assigned_to'].queryset = User.objects.filter(role='media_team').exclude(pk=assignment.assigned_to.pk)
    
    return render(request, 'requests/reassign.html', {'form': form, 'assignment': assignment, 'service_request': service_request})
