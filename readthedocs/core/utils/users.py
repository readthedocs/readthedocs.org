from django.contrib.auth.models import User

def get_user_by_username_or_email(username_or_email):
    """Get a user by their username or email address."""
    # SECURITY: Check for email address if the username contains an "@" symbol,
    # to prevent fetching a user with an username that matches
    # the email address of another user (GHSA-4392-6mf4-pf5p).
    if "@" in username_or_email:
        return User.objects.filter(
            emailaddress__verified=True, emailaddress__email=username_or_email
        ).first()
    return User.objects.filter(username=username_or_email).first()
