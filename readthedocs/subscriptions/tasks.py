"""Organization tasks."""
import datetime

import structlog
from django.contrib.auth.models import User
from django.db.models import Count
from django.http import HttpRequest
from django.utils import timezone

from readthedocs.builds.models import Build
from readthedocs.core.utils import send_email
from readthedocs.organizations.models import Organization
from readthedocs.projects.models import Domain, Project
from readthedocs.subscriptions.models import Subscription
from readthedocs.subscriptions.notifications import (
    OrganizationDisabledNotification,
    SubscriptionEndedNotification,
    SubscriptionRequiredNotification,
    TrialEndingNotification,
)
from readthedocs.worker import app


log = structlog.get_logger(__name__)


@app.task(queue='web')
def daily_email():
    """Daily email beat task for organization notifications."""
    notifications = (
        TrialEndingNotification,
        SubscriptionRequiredNotification,
        SubscriptionEndedNotification,
        OrganizationDisabledNotification,
    )

    orgs_sent = Organization.objects.none()

    for cls in notifications:
        orgs = cls.for_organizations().exclude(id__in=orgs_sent).distinct()
        orgs_sent |= orgs
        for org in orgs:
            log.info(
                'Sending notification',
                notification_name=cls.name,
                organization_slug=org.slug,
            )
            for owner in org.owners.all():
                notification = cls(
                    context_object=org,
                    request=HttpRequest(),
                    user=owner,
                )
                log.info('Notification sent.', recipient=owner)
                notification.send()


@app.task(queue='web')
def disable_organization_expired_trials():
    """Daily task to disable organization with expired Trial Plans."""
    queryset = Organization.objects.subscription_trial_plan_ended()

    for organization in queryset:
        log.info(
            'Organization disabled due to trial ended.',
            organization_slug=organization.slug,
        )
        organization.disabled = True
        organization.save()


@app.task(queue='web')
def weekly_subscription_stats_email(recipients=None):
    """
    Weekly email to communicate stats about subscriptions.

    :param list recipients: List of emails to send the stats to.
    """
    if not recipients:
        log.info('No recipients to send stats to.')
        return

    last_week = timezone.now() - datetime.timedelta(weeks=1)
    yesterday = timezone.now() - datetime.timedelta(days=1)

    projects = Project.objects.filter(pub_date__gte=last_week).count()
    builds = Build.objects.filter(date__gte=last_week).count()
    organizations = Organization.objects.filter(pub_date__gte=last_week).count()
    domains = Domain.objects.filter(created__gte=last_week).count()
    organizations_to_disable = Organization.objects.disable_soon(days=30).count()
    users = User.objects.filter(date_joined__gte=last_week).count()
    subscriptions = (
        Subscription.objects
        .filter(
            trial_end_date__gte=last_week,
            trial_end_date__lte=yesterday,
        )
        .values('status', 'plan__name')
        .annotate(total_status=Count('status'))
        .order_by('status')
    )
    context = {
        'projects': projects,
        'builds': builds,
        'organizations': organizations,
        'domains': domains,
        'organizations_to_disable': organizations_to_disable,
        'users': users,
        'subscriptions': list(subscriptions),
    }

    log.info('Sending weekly subscription stats email.')
    send_email(
        from_email='Read the Docs <no-reply@readthedocs.com>',
        subject='Weekly subscription stats',
        recipient=recipients[0],
        template='subscriptions/notifications/subscription_stats_email.txt',
        template_html=None,
        context=context,
        # Use ``cc`` here because our ``send_email`` does not accept a list of recipients
        cc=recipients[1:],
    )
