"""Utilities for organizations."""

import structlog

from readthedocs.core.utils import send_email


log = structlog.get_logger(__name__)


def send_team_add_email(team_member, request):
    """Send an organization team add email."""
    log.info(
        "Sending team add notification.",
        team=team_member.team,
        email=team_member.member.email,
    )
    send_email(
        team_member.member.email,
        subject="Join your team at Read the Docs",
        template="organizations/email/team_add.txt",
        template_html="organizations/email/team_add.html",
        context={
            "sender_full_name": request.user.get_full_name(),
            "sender_username": request.user.username,
            "organization_name": team_member.team.organization.name,
            "organization_slug": team_member.team.organization.slug,
        },
        request=request,
    )
