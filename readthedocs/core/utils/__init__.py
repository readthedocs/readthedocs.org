"""Common utilty functions"""

from __future__ import absolute_import

import errno
import getpass
import logging
import os
import re

from django.conf import settings
from django.utils import six
from django.utils.functional import allow_lazy
from django.utils.safestring import SafeText, mark_safe
from django.utils.text import slugify as slugify_base
from future.backports.urllib.parse import urlparse

from ..tasks import send_email_task
from readthedocs.builds.constants import LATEST
from readthedocs.doc_builder.constants import DOCKER_LIMITS


log = logging.getLogger(__name__)

SYNC_USER = getattr(settings, 'SYNC_USER', getpass.getuser())


def broadcast(type, task, args, kwargs=None):  # pylint: disable=redefined-builtin
    assert type in ['web', 'app', 'build']
    if kwargs is None:
        kwargs = {}
    default_queue = getattr(settings, 'CELERY_DEFAULT_QUEUE', 'celery')
    if type in ['web', 'app']:
        servers = getattr(settings, "MULTIPLE_APP_SERVERS", [default_queue])
    elif type in ['build']:
        servers = getattr(settings, "MULTIPLE_BUILD_SERVERS", [default_queue])
    for server in servers:
        task.apply_async(
            queue=server,
            args=args,
            kwargs=kwargs,
        )


def clean_url(url):
    parsed = urlparse(url)
    if parsed.scheme or parsed.netloc:
        return parsed.netloc
    return parsed.path


def cname_to_slug(host):
    from dns import resolver
    answer = [ans for ans in resolver.query(host, 'CNAME')][0]
    domain = answer.target.to_unicode()
    slug = domain.split('.')[0]
    return slug


def trigger_build(project, version=None, record=True, force=False, basic=False):
    """Trigger build for project and version

    If project has a ``build_queue``, execute task on this build queue. Queue
    will be prefixed with ``build-`` to unify build queue names.
    """
    # Avoid circular import
    from readthedocs.projects.tasks import update_docs
    from readthedocs.builds.models import Build

    if project.skip:
        return None

    if not version:
        version = project.versions.get(slug=LATEST)

    kwargs = dict(
        pk=project.pk,
        version_pk=version.pk,
        record=record,
        force=force,
        basic=basic,
    )

    build = None
    if record:
        build = Build.objects.create(
            project=project,
            version=version,
            type='html',
            state='triggered',
            success=True,
        )
        kwargs['build_pk'] = build.pk

    options = {}
    if project.build_queue:
        options['queue'] = project.build_queue

    # Set per-task time limit
    time_limit = DOCKER_LIMITS['time']
    try:
        if project.container_time_limit:
            time_limit = int(project.container_time_limit)
    except ValueError:
        pass
    # Add 20% overhead to task, to ensure the build can timeout and the task
    # will cleanly finish.
    options['soft_time_limit'] = time_limit
    options['time_limit'] = int(time_limit * 1.2)

    update_docs.apply_async(kwargs=kwargs, **options)

    return build


def send_email(recipient, subject, template, template_html, context=None,
               request=None):  # pylint: disable=unused-argument
    """Alter context passed in and call email send task

    .. seealso::

        Task :py:func:`readthedocs.core.tasks.send_email_task`
            Task that handles templating and sending email message
    """
    if context is None:
        context = {}
    context['uri'] = '{scheme}://{host}'.format(
        scheme='https', host=settings.PRODUCTION_DOMAIN)
    send_email_task.delay(recipient, subject, template, template_html, context)


def slugify(value, *args, **kwargs):
    """Add a DNS safe option to slugify

    :param dns_safe: Remove underscores from slug as well
    """
    dns_safe = kwargs.pop('dns_safe', True)
    value = slugify_base(value, *args, **kwargs)
    if dns_safe:
        value = mark_safe(re.sub('[-_]+', '-', value))
    return value


slugify = allow_lazy(slugify, six.text_type, SafeText)


def safe_makedirs(directory_name):
    """
    Safely create a directory.

    Makedirs has an issue where it has a race condition around
    checking for a directory and then creating it.
    This catches the exception in the case where the dir already exists.
    """
    try:
        os.makedirs(directory_name)
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass
        raise
