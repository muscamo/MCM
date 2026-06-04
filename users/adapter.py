from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialAccount


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # This is called before a social login is processed
        # You can customize user creation or data mapping here
        pass

    def save_user(self, request, sociallogin, form=None):
        # This is called when saving a user from social login
        user = super().save_user(request, sociallogin, form)
        
        # Extract Google OAuth data
        if sociallogin.account.provider == 'google':
            extra_data = sociallogin.account.extra_data
            user.google_id = extra_data.get('sub')
            user.google_picture_url = extra_data.get('picture')
            user.google_verified_email = extra_data.get('email_verified', False)
            user.save()
        
        return user


class CustomAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        # This is called when saving a user from regular registration
        user = super().save_user(request, user, form, commit=False)
        # You can add custom logic here if needed
        if commit:
            user.save()
        return user
