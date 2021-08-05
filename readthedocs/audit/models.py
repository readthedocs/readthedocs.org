"""Audit models."""

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.models import TimeStampedModel

from readthedocs.acl.utils import get_auth_backend


class AuditLogManager(models.Manager):

    """AuditLog manager."""

    def new(self, action, user=None, request=None, **kwargs):
        """
        Create an audit log for `action`.

        If user or request are given,
        other fields will be auto-populated from that information.
        """

        actions_requiring_user = (AuditLog.PAGEVIEW, AuditLog.AUTHN, AuditLog.LOGOUT)
        if action in actions_requiring_user and (not user or not request):
            raise TypeError(f'A user and a request is required for the {action} action.')
        if action == AuditLog.PAGEVIEW and 'project' not in kwargs:
            raise TypeError(f'A project is required for the {action} action.')

        # Don't save anonymous users.
        if user and user.is_anonymous:
            user = None

        if request:
            kwargs['ip'] = request.META.get('REMOTE_ADDR')
            kwargs['browser'] = request.headers.get('User-Agent')
            kwargs.setdefault('resource', request.path_info)
            kwargs.setdefault('auth_backend', get_auth_backend(request))

        return self.create(
            user=user,
            action=action,
            **kwargs,
        )


class AuditLog(TimeStampedModel):

    """
    Track user actions for audit purposes.

    A log can be attached to a user and/or project.
    If the user or project are deleted the log will be preserved,
    and the deleted user/project can be accessed via the ``log_*`` attributes.
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
    log_user_username = models.CharField(
        _('Username'),
        max_length=150,
        blank=True,
        null=True,
        db_index=True,
    )

    project = models.ForeignKey(
        'projects.Project',
        verbose_name=_('Project'),
        null=True,
        db_index=True,
        on_delete=models.SET_NULL,
    )
    # Extra information in case the project is deleted.
    log_project_id = models.IntegerField(
        _('Project ID'),
        blank=True,
        null=True,
        db_index=True,
    )
    log_project_slug = models.CharField(
        _('Project slug'),
        max_length=63,
        blank=True,
        null=True,
        db_index=True,
    )

    action = models.CharField(
        _('Action'),
        max_length=150,
        choices=CHOICES,
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

    def save(self, **kwargs):
        if self.user:
            self.log_user_id = self.user.id
            self.log_user_username = self.user.username
        if self.project:
            self.log_project_id = self.project.id
            self.log_project_slug = self.project.slug
        super().save(**kwargs)

    def __str__(self):
        return self.action
