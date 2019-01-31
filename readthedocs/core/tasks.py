# -*- coding: utf-8 -*-

"""Basic tasks."""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.utils import timezone
from messages_extends.models import Message as PersistentMessage

from readthedocs.worker import app


log = logging.getLogger(__name__)

EMAIL_TIME_LIMIT = 30


@app.task(queue='web', time_limit=EMAIL_TIME_LIMIT)
def send_email_task(
        recipient, subject, template, template_html, context=None,
        from_email=None, **kwargs
):
    """
    Send multipart email.

    recipient
        Email recipient address

    subject
        Email subject header

    template
        Plain text template to send

    template_html
        HTML template to send as new message part

    context
        A dictionary to pass into the template calls

    kwargs
        Additional options to the EmailMultiAlternatives option.
    """
    msg = EmailMultiAlternatives(
        subject,
        get_template(template).render(context), from_email or
        settings.DEFAULT_FROM_EMAIL,
        [recipient], **kwargs
    )
    try:
        msg.attach_alternative(
            get_template(template_html).render(context),
            'text/html',
        )
    except TemplateDoesNotExist:
        pass
    msg.send()
    log.info('Sent email to recipient: %s', recipient)


@app.task(queue='web')
def clear_persistent_messages():
    # Delete all expired message_extend's messages
    log.info("Deleting all expired message_extend's messages")
    expired_messages = PersistentMessage.objects.filter(
        expires__lt=timezone.now(),
    )
    expired_messages.delete()
