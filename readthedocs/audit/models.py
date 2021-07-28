from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.models import TimeStampedModel


class AuditLogManager(models.Manager):

    def new(self, action, user=None, request=None, **kwargs):
        """
        Create an audit log for `action`.

        If user or request are given,
        other fields will be auto-populated from that information.
        """

        actions_requiring_user = (AuditLog.PAGEVIEW, AuditLog.AUTHN, AuditLog.LOGOUT)
        if action in actions_requiring_user and (not user or not request):
            raise TypeError(f'A user and a request is required for the {action} action.')
        if action == AuditLog.PAGEVIEW and not 'project' in kwargs:
            raise TypeError(f'A project is required for the {action} action.')

        if user:
            kwargs.setdefault('auth_backend', getattr(user, 'backend', None))
            if user.is_authenticated:
                kwargs['log_user_id'] = user.id
                kwargs['log_username'] = user.username
            else:
                user = None

        if request:
            kwargs['ip'] = request.META.get('REMOTE_ADDR')
            kwargs['browser'] = request.headers.get('User-Agent')
            kwargs.setdefault('resource', request.path_info)

        return self.create(
            user=user,
            action=action,
            **kwargs,
        )


class AuditLog(TimeStampedModel):
    """
    Track user actions for audit purposes.

    A log can be attached to a user and/or project.
    Logs attached to a project will be deleted when the project is deleted.

    If the user is deleted the log will be preserved,
    and the deleted user can be accessed via ``log_user_id`` and ``log_username``.
    """

    PAGEVIEW = 'pageview'
    AUTHN = 'authentication'
    AUTHN_FAILURE = 'authentication-failure'
    LOGOUT = 'log-out'

    CHOICES = (
        (PAGEVIEW, 'Page view'),
        (AUTHN, 'Authentication'),
        (AUTHN_FAILURE, 'Authentication failure'),
        (LOGOUT, 'Log out'),
    )

    user = models.ForeignKey(
        User,
        verbose_name=_('User'),
        null=True,
        on_delete=models.SET_NULL,
        db_index=True,
    )
    # Extra information in case the user is deleted.
    log_user_id = models.IntegerField(
        _('User ID'),
        blank=True,
        null=True,
        db_index=True,
    )
    log_username = models.CharField(
        _('Username'),
        max_length=150,
        blank=True,
        null=True,
        db_index=True,
    )

    action = models.CharField(
        _('Action'),
        max_length=150,
        choices=CHOICES,
    )
    project = models.ForeignKey(
        'projects.Project',
        verbose_name=_('Project'),
        null=True,
        db_index=True,
        on_delete=models.CASCADE,
    )
    auth_backend = models.CharField(
        _('Auth backend'),
        max_length=250,
        blank=True,
        null=True,
    )
    ip = models.GenericIPAddressField(
        _('IP address'),
        blank=True,
        null=True,
    )
    browser = models.CharField(
        _('Browser user-agent'),
        max_length=250,
        blank=True,
        null=True,
    )
    # Resource can be a path,
    # set it slightly greater than ``HTMLFile.path``.
    resource = models.CharField(
        _('Resource'),
        max_length=5500,
        blank=True,
        null=True,
    )

    objects = AuditLogManager()
