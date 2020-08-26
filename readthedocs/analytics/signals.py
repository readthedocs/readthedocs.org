"""Django signals for the analytics app."""
from django.db.models import F
from django.dispatch import receiver
from django.utils import timezone

from readthedocs.api.v2.signals import footer_response
from readthedocs.core.unresolver import unresolve_from_request
from readthedocs.projects.models import Feature

from .models import PageView


@receiver(footer_response)
def increase_page_view_count(sender, *, request, context, absolute_uri, **kwargs):
    """Increase the page view count for the given project."""
    # unused
    del sender
    del kwargs

    project = context['project']
    version = context['version']

    if not absolute_uri or not project.has_feature(Feature.STORE_PAGEVIEWS):
        return

    unresolved = unresolve_from_request(request, absolute_uri)
    if not unresolved:
        return

    path = unresolved.filename

    fields = dict(
        project=project,
        version=version,
        path=path,
        date=timezone.now().date(),
    )

    page_view = PageView.objects.filter(**fields).first()
    if page_view:
        page_view.view_count = F('view_count') + 1
        page_view.save(update_fields=['view_count'])
    else:
        PageView.objects.create(**fields, view_count=1)
