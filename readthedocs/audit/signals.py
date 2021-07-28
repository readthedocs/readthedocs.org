from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.dispatch import receiver

from readthedocs.audit.models import AuditLog


@receiver(user_logged_in)
def log_logged_in(sender, request, user, **kwargs):
    AuditLog.objects.new(
        action=AuditLog.AUTHN,
        user=user,
        request=request,
    )

@receiver(user_logged_out)
def log_logged_out(sender, request, user, **kwargs):
    AuditLog.objects.new(
        action=AuditLog.LOGOUT,
        user=user,
        request=request,
    )

@receiver(user_login_failed)
def log_login_failed(sender, credentials, request, **kwargs):
    AuditLog.objects.new(
        action=AuditLog.AUTHN_FAILURE,
        request=request,
    )
