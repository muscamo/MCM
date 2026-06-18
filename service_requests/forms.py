from django import forms
from .models import ServiceRequest, ServiceType, Department, Assignment, RequestComment, RequestAttachment


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class ServiceTypeForm(forms.ModelForm):
    class Meta:
        model = ServiceType
        fields = ['name', 'description', 'requires_team_assignment', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class ServiceRequestForm(forms.ModelForm):
    class Meta:
        model = ServiceRequest
        fields = [
            'title', 'description', 'service_type', 'department',
            'event_date', 'event_time', 'deadline', 'priority',
            'location', 'expected_attendees', 'special_requirements'
        ]
        widgets = {
            'event_date': forms.DateInput(attrs={'type': 'date'}),
            'event_time': forms.TimeInput(attrs={'type': 'time'}),
            'deadline': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'special_requirements': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.is_department_staff():
            # Filter departments to only show user's departments
            self.fields['department'].queryset = user.departments.all()
        
        # Filter service types to only show active ones
        self.fields['service_type'].queryset = ServiceType.objects.filter(is_active=True)


class ServiceRequestApprovalForm(forms.Form):
    action = forms.ChoiceField(
        choices=[('approve', 'Approve'), ('reject', 'Reject')],
        widget=forms.RadioSelect
    )
    rejection_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Reason for rejection (required if rejecting)'}),
        help_text='Required if rejecting the request'
    )
    assign_to = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text='Select media team members to assign (required if approving)'
    )
    assign_to_all = forms.BooleanField(
        required=False,
        label='Assign to all media team members'
    )


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['assigned_to', 'notes', 'is_primary']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class ReassignForm(forms.Form):
    assigned_to = forms.ModelChoiceField(
        queryset=None,
        empty_label="Select team member",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Add notes about the reassignment...'})
    )


class ProgressUpdateForm(forms.Form):
    progress_percentage = forms.IntegerField(
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={'type': 'range', 'class': 'form-range'}),
        help_text='Progress percentage (0-100)'
    )
    progress_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Add progress notes...'})
    )


class RequestCommentForm(forms.ModelForm):
    class Meta:
        model = RequestComment
        fields = ['comment', 'is_internal']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Add a comment...'}),
        }


class RequestAttachmentForm(forms.ModelForm):
    class Meta:
        model = RequestAttachment
        fields = ['file', 'description']
