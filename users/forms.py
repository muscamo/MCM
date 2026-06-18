from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from service_requests.models import Department


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        required=True,
        help_text='Select your role in the organization'
    )
    departments = forms.ModelMultipleChoiceField(
        queryset=Department.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text='Select your departments (required for Department Staff)'
    )
    phone = forms.CharField(max_length=20, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'departments', 'phone', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name != 'departments':
                field.widget.attrs['class'] = 'form-control'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already in use.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        departments = cleaned_data.get('departments')

        if role in ['department_staff', 'departmental_director'] and not departments:
            raise forms.ValidationError('At least one department is required for Department Staff and Departmental Director roles.')

        return cleaned_data


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'role', 'departments', 'phone', 'profile_picture']
        widgets = {
            'profile_picture': forms.FileInput(attrs={'class': 'form-control-file'}),
            'departments': forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        is_admin = kwargs.pop('is_admin', False)
        super().__init__(*args, **kwargs)
        
        # Regular users cannot change email, role, or departments
        if not is_admin:
            self.fields.pop('email', None)
            self.fields.pop('role', None)
            self.fields.pop('departments', None)
        
        for field_name, field in self.fields.items():
            if field_name not in ['profile_picture', 'departments']:
                field.widget.attrs['class'] = 'form-control'
