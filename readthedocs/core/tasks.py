"""Basic tasks."""

import structlog
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
from messages_extends.models import Message as PersistentMessage

from readthedocs.worker import app

log = structlog.get_logger(__name__)

EMAIL_TIME_LIMIT = 30


@app.task(queue='web', time_limit=EMAIL_TIME_LIMIT)
def send_email_task(
    recipient, subject, content, content_html=None, from_email=None, **kwargs
):
    """
    Send multipart email.

    recipient
        Email recipient address

    subject
        Email subject header

    content
        Plain text template to send

    content_html
        HTML content to send as new message part

    kwargs
        Additional options to the EmailMultiAlternatives option.
    """
    msg = EmailMultiAlternatives(
        subject,
        content,
        from_email or settings.DEFAULT_FROM_EMAIL,
        [recipient],
        **kwargs
    )
    if content_html:
        msg.attach_alternative(content_html, "text/html")
    log.info("Sending email to recipient.", recipient=recipient)
    msg.send()


@app.task(queue='web')
def clear_persistent_messages():
    # Delete all expired message_extend's messages
    log.info("Deleting all expired message_extend's messages")
    expired_messages = PersistentMessage.objects.filter(
        expires__lt=timezone.now(),
    )
    expired_messages.delete()
