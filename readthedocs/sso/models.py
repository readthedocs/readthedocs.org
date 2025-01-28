"""Single Sign On models."""

import uuid

from django.db import models

from readthedocs.projects.validators import validate_domain_name


class SSOIntegration(models.Model):

    """Single Sign-On integration for an Organization."""

    PROVIDER_ALLAUTH = "allauth"
    PROVIDER_EMAIL = "email"
    PROVIDER_SAML = "saml"
    PROVIDER_CHOICES = (
        (PROVIDER_ALLAUTH, "AllAuth"),
        (PROVIDER_EMAIL, "Email"),
        (PROVIDER_SAML, "SAML"),
    )

    name = models.CharField(
        max_length=128,
        null=True,
        blank=True,
    )
    token = models.UUIDField(
        unique=True,
        default=uuid.uuid4,
        # editable=False,
    )
    organization = models.OneToOneField(
        "organizations.Organization",
        on_delete=models.CASCADE,
    )
    provider = models.CharField(
        choices=PROVIDER_CHOICES,
        max_length=32,
    )

    saml_app = models.OneToOneField(
        "socialaccount.SocialApp",
        related_name="sso_integration",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    domains = models.ManyToManyField(
        "sso.SSODomain",
        related_name="ssointegrations",
        blank=True,
    )

    def __str__(self):
        return self.name or self.provider


class SSODomain(models.Model):
    domain = models.CharField(
        unique=True,
        max_length=128,
        validators=[validate_domain_name],
    )

    def __str__(self):
        return self.domain
