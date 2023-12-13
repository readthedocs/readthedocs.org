"""Notifications related to custom domains."""

from readthedocs.notifications import EmailNotification


class PendingCustomDomainValidation(EmailNotification):
    app_templates = "domains"
    context_object_name = "domain"
    name = "pending_domain_configuration"
    subject = "Pending configuration of custom domain {{ domain.domain }}"
