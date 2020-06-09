"""Django signals for the analytics app."""
from django.db.models import F
from django.dispatch import receiver
from django.utils import timezone

from readthedocs.api.v2.signals import footer_response
from readthedocs.projects.models import Feature

from .models import PageView


@receiver(footer_response)
def increase_page_view_count(sender, **kwargs):
    """Increase the page view count for the given project."""
    del sender  # unused
    context = kwargs['context']

    project = context['project']
    version = context['version']
    # footer_response sends an empty path for the index
    path = context['path'] or '/'

    if project.has_feature(Feature.STORE_PAGEVIEWS):
        page_view, _ = PageView.objects.get_or_create(
            project=project,
            version=version,
            path=path,
            date=timezone.now().date(),
        )
        PageView.objects.filter(pk=page_view.pk).update(
            view_count=F('view_count') + 1
        )
