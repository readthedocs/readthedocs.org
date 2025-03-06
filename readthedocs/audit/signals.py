"""Audit signals."""

from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in
from django.contrib.auth.signals import user_logged_out
from django.contrib.auth.signals import user_login_failed
from django.db.models import Q
from django.dispatch import receiver

from readthedocs.audit.models import AuditLog


@receiver(user_logged_in)
def log_logged_in(sender, request, user, **kwargs):
    """Log when a user has logged in."""
    # pylint: disable=unused-argument
    AuditLog.objects.new(
        action=AuditLog.AUTHN,
        user=user,
        request=request,
    )


@receiver(user_logged_out)
def log_logged_out(sender, request, user, **kwargs):
    """Log when a user has logged out."""
    # pylint: disable=unused-argument
    # Only log if there is an user.
    if not user:
        return
    AuditLog.objects.new(
        action=AuditLog.LOGOUT,
        user=user,
        request=request,
    )


@receiver(user_login_failed)
def log_login_failed(sender, credentials, request, **kwargs):
    """Log when a user has failed to logged in."""
    # pylint: disable=unused-argument
    username = credentials.get("username")
    user = User.objects.filter(Q(username=username) | Q(email=username)).first()
    AuditLog.objects.new(
        action=AuditLog.AUTHN_FAILURE,
        user=user,
        log_user_username=username,
        request=request,
    )
