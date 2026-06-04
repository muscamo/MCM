# Media Center Manager

A Django + HTMX application for managing media center service requests. This system allows different departments to place requests for media services, which can be approved and assigned by the communication director to media team members.

## Features

- **Role-Based Access Control**: Three user roles - Department Staff, Communication Director, and Media Team
- **Service Request Management**: Submit, approve, assign, and track service requests
- **Email Notifications**: Automatic email notifications for request updates
- **In-App Notifications**: Real-time notification system within the application
- **Progress Tracking**: Track progress on assigned tasks with percentage completion
- **Comments & Attachments**: Add comments and file attachments to requests
- **HTMX Integration**: Dynamic, responsive UI without page reloads
- **Modern UI**: Built with Tailwind CSS and Bootstrap 5

## Service Types Supported

- Recording for interviews
- Recording for reports
- TV series production
- Live streaming
- Photography for social media
- Graphic design of flyers
- Graphic design of booklets
- Social media posts
- And more...

## User Roles

### Department Staff
- Submit new service requests
- View and track their own requests
- Add comments and attachments
- Receive notifications on request updates

### Communication Director
- View all pending requests
- Approve or reject requests
- Assign media team members to requests
- View all requests and their status
- Manage the overall workflow

### Media Team Members
- View assigned requests
- Update progress on assigned tasks
- Add comments and attachments
- Receive notifications on new assignments

## Installation

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Setup Steps

1. **Clone the repository**
   ```bash
   cd /Users/mauriceg/Projects/mediaCenterManager/CascadeProjects/windsurf-project
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up environment variables**
   Create a `.env` file in the project root with the following variables:
   ```
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   DEFAULT_FROM_EMAIL=noreply@mediacenter.com
   ```

6. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

7. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

8. **Create initial data**
   Run the Django shell to create initial departments and service types:
   ```bash
   python manage.py shell
   ```
   
   Then run:
   ```python
   from requests.models import Department, ServiceType
   
   # Create departments
   dept1 = Department.objects.create(name='Marketing', description='Marketing department')
   dept2 = Department.objects.create(name='Human Resources', description='HR department')
   dept3 = Department.objects.create(name='IT', description='IT department')
   
   # Create service types
   ServiceType.objects.create(name='Recording for Interviews', description='Interview recording services')
   ServiceType.objects.create(name='Recording for Reports', description='Report recording services')
   ServiceType.objects.create(name='TV Series', description='TV series production')
   ServiceType.objects.create(name='Live Streaming', description='Live streaming services')
   ServiceType.objects.create(name='Photography for Socials', description='Social media photography')
   ServiceType.objects.create(name='Graphic Design - Flyer', description='Flyer design services')
   ServiceType.objects.create(name='Graphic Design - Booklet', description='Booklet design services')
   ServiceType.objects.create(name='Social Media Posts', description='Social media post creation')
   
   exit()
   ```

9. **Run the development server**
   ```bash
   python manage.py runserver
   ```

10. **Access the application**
    Open your browser and navigate to `http://localhost:8000`

## Usage

### First-Time Setup

1. **Register users**: Go to `/users/register/` to register users with appropriate roles
   - Create at least one Communication Director
   - Create Media Team members
   - Create Department Staff members

2. **Create departments and service types**: Use the Django admin at `/admin/` to manage departments and service types

### Workflow

1. **Department Staff** submits a service request with details about the event/program
2. **Communication Director** reviews pending requests and either approves or rejects them
3. If approved, the **Communication Director** assigns one or more **Media Team members** to the request
4. **Media Team members** receive notifications and can view their assigned tasks
5. **Media Team members** update progress as they work on the request
6. **Department Staff** can track progress and add comments for clarification
7. When complete, the request is marked as completed and the requester is notified

## Project Structure

```
windsurf-project/
├── manage.py
├── requirements.txt
├── media_center/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── requests/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
├── users/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
├── notifications/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
├── templates/
│   ├── base.html
│   ├── requests/
│   │   ├── dashboard.html
│   │   ├── request_list.html
│   │   ├── request_form.html
│   │   ├── request_detail.html
│   │   ├── request_approve.html
│   │   ├── request_assign.html
│   │   ├── progress_update.html
│   │   ├── comment_list.html
│   │   └── attachment_list.html
│   ├── users/
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── profile.html
│   │   └── logout.html
│   └── notifications/
│       └── notification_list.html
└── README.md
```

## Email Configuration

For email notifications to work properly, configure your email settings in the `.env` file:

- **Gmail**: Use an App Password (not your regular password)
- **Other providers**: Configure SMTP settings accordingly

In development, emails are logged to the console. In production, set `EMAIL_BACKEND` to `django.core.mail.backends.smtp.EmailBackend`.

## Deployment

### Production Considerations

1. **Set DEBUG=False** in your `.env` file
2. **Use a strong SECRET_KEY**
3. **Configure ALLOWED_HOSTS** with your domain
4. **Use a production database** (PostgreSQL recommended)
5. **Configure static file serving** (whitenoise or similar)
6. **Use a production web server** (Gunicorn + Nginx)
7. **Configure HTTPS** with SSL certificates
8. **Set up proper email backend** for production

### Example Production Settings

```python
DEBUG=False
SECRET_KEY=your-very-strong-secret-key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://user:password@localhost/dbname
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
```

## Technologies Used

- **Django 5.0.4**: Web framework
- **HTMX 1.17.2**: Dynamic HTML interactions
- **Bootstrap 5**: UI framework
- **Tailwind CSS**: Utility-first CSS framework
- **django-htmx**: Django-HTMX integration
- **django-crispy-forms**: Form rendering
- **python-decouple**: Configuration management

## Admin Access

Access the Django admin panel at `/admin/` to manage:
- Users and roles
- Departments
- Service types
- All service requests
- Assignments
- Comments and attachments
- Notifications

## Support

For issues or questions, please contact the development team.

## License

This project is proprietary software for the Media Center.
