import logging

from readthedocs.core.utils import send_email


log = logging.getLogger(__name__)


def send_team_invite_email(invite, request):
    """Send an organization team invite email."""
    log.info('Sending team invite for %s to %s', invite.team, invite.email)
    send_email(
        invite.email,
        subject='Join your team at Read the Docs',
        template='organizations/email/team_invite.txt',
        template_html='organizations/email/team_invite.html',
        context={
            'invite_hash': invite.hash,
            'sender_full_name': request.user.get_full_name(),
            'sender_username': request.user.username,
            'organization_name': invite.organization.name,
        },
        request=request,
    )


def send_team_add_email(team_member, request):
    """Send an organization team add email."""
    log.info(
        'Sending team add notification for %s to %s',
        team_member.team,
        team_member.member.email,
    )
    send_email(
        team_member.member.email,
        subject='Join your team at Read the Docs',
        template='organizations/email/team_add.txt',
        template_html='organizations/email/team_add.html',
        context={
            'sender_full_name': request.user.get_full_name(),
            'sender_username': request.user.username,
            'organization_name': team_member.team.organization.name,
            'organization_slug': team_member.team.organization.slug,
        },
        request=request,
    )
