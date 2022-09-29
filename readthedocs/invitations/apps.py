"""
Invitations app.

This manages user invitations to join a project, organization, team, etc.
"""

from django.apps import AppConfig


class InvitationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "readthedocs.invitations"

    def ready(self):
        import readthedocs.invitations.signals  # noqa
