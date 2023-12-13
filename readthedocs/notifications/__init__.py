"""Notification system to send email/site messages to users."""
from .notification import EmailNotification, SiteNotification

__all__ = (
    "EmailNotification",
    "SiteNotification",  # TODO: remove this
)
