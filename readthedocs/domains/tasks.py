"""Tasks related to custom domains."""

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from readthedocs.core.permissions import AdminPermission
from readthedocs.domains.notifications import MESSAGE_DOMAIN_VALIDATION_PENDING
from readthedocs.domains.notifications import PendingCustomDomainValidation
from readthedocs.notifications.models import Notification
from readthedocs.projects.models import Domain
from readthedocs.worker import app


@app.task(queue="web")
def email_pending_custom_domains(number_of_emails=3):
    """
    Send a total of `number_of_emails` to a user about a pending custom domain.

    The emails are send exponentially till the last day,
    for 30 days this would be: 7, 15, 30.
    """
    now = timezone.now().date()
    validation_period = settings.RTD_CUSTOM_DOMAINS_VALIDATION_PERIOD
    dates = [
        now - timezone.timedelta(days=validation_period // (2**n)) for n in range(number_of_emails)
    ]
    queryset = Domain.objects.pending(include_recently_expired=True).filter(
        validation_process_start__date__in=dates
    )
    for domain in queryset:
        # NOTE: this site notification was attach to every single user.
        # The new behavior is to attach it to the project.
        #
        # We send an email notification to all the project's admins.
        Notification.objects.add(
            message_id=MESSAGE_DOMAIN_VALIDATION_PENDING,
            attached_to=domain.project,
            dismissable=True,
            format_values={
                "domain": domain.domain,
                "domain_url": reverse(
                    "projects_domains_edit", args=[domain.project.slug, domain.pk]
                ),
            },
        )

        for user in AdminPermission.admins(domain.project):
            notification = PendingCustomDomainValidation(
                context_object=domain,
                user=user,
            )
            notification.send()
