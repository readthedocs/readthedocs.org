"""Subscription models."""

from datetime import timedelta

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from readthedocs.core.history import ExtraHistoricalRecords
from readthedocs.core.utils import slugify
from readthedocs.organizations.models import Organization
from readthedocs.subscriptions.constants import FEATURE_TYPES


class Plan(models.Model):

    """Organization subscription plans."""

    # Auto fields
    pub_date = models.DateTimeField(_('Publication date'), auto_now_add=True)
    modified_date = models.DateTimeField(_('Modified date'), auto_now=True)

    # Local
    name = models.CharField(_('Name'), max_length=100)
    description = models.CharField(
        _('Description'),
        max_length=255,
        null=True,
        blank=True,
    )
    slug = models.SlugField(_('Slug'), max_length=255, unique=True)
    stripe_id = models.CharField(_('Stripe ID'), max_length=100)
    price = models.IntegerField(_('Price'))
    trial = models.IntegerField(_('Trial'))

    # Foreign
    for_organizations = models.ManyToManyField(
        Organization,
        verbose_name=_('For organizations'),
        related_name='available_plans',
        blank=True,
        # Custom table is used, because these models were moved from an existing app.
        db_table='organizations_plan_for_organizations',
    )

    published = models.BooleanField(
        _('Published'),
        default=False,
        help_text="<b>Warning</b>: This will make this subscription available for users to buy. Don't add unless you're sure."  # noqa
    )

    class Meta:
        # Custom table is used, because these models were moved from an existing app.
        db_table = 'organizations_plan'
        ordering = ('price',)

    def get_absolute_url(self):
        return reverse(
            'organization_plan_detail',
            args=(self.organizations.all()[0].slug, self.slug),
        )

    def __str__(self):
        return f"{self.name} ({self.stripe_id})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class PlanFeature(models.Model):

    """
    Plan Feature.

    Useful for plan display, onboarding steps and other actions.
    """

    class Meta:
        # Custom table is used, because these models were moved from an existing app.
        db_table = 'organizations_planfeature'
        unique_together = (('plan', 'feature_type'),)

    # Auto fields
    pub_date = models.DateTimeField(_('Publication date'), auto_now_add=True)
    modified_date = models.DateTimeField(_('Modified date'), auto_now=True)

    plan = models.ForeignKey(
        Plan,
        related_name='features',
        on_delete=models.CASCADE,
    )
    feature_type = models.CharField(_("Type"), max_length=32, choices=FEATURE_TYPES)
    value = models.IntegerField(_("Numeric value"), null=True, blank=True)
    description = models.CharField(
        _('Description'),
        max_length=255,
        null=True,
        blank=True,
    )

    def __str__(self):
        return '{plan} feature: {feature}'.format(
            plan=self.plan,
            feature=self.get_feature_type_display(),
        )

    @property
    def description_display(self):
        return self.description or self.get_feature_type_display()


class Subscription(models.Model):

    """
    Organization subscription model.

    .. note::

        ``status``, ``trial_end_date`` and maybe other fields are updated by
        Stripe by hitting a webhook in our service hanlded by
        ``StripeEventView``.
    """

    plan = models.ForeignKey(
        Plan,
        verbose_name=_('Plan'),
        related_name='subscriptions',
        on_delete=models.CASCADE,
    )
    organization = models.OneToOneField(
        Organization,
        verbose_name=_('Organization'),
        on_delete=models.CASCADE,
    )
    locked = models.BooleanField(
        _('Locked plan'),
        default=False,
        help_text=_('Locked plan for custom contracts'),
    )
    modified_date = models.DateTimeField(_('Modified date'), auto_now=True)

    # These fields (stripe_id, status, start_date and end_date) are filled with
    # the data retrieved from Stripe after the creation of the model instance.
    stripe_id = models.CharField(
        _('Stripe subscription ID'),
        max_length=100,
        blank=True,
        null=True,
    )
    status = models.CharField(_('Subscription status'), max_length=16)
    start_date = models.DateTimeField(_('Start date'), blank=True, null=True)
    end_date = models.DateTimeField(
        _('End date'),
        blank=True,
        null=True,
    )

    trial_end_date = models.DateTimeField(
        _('Trial end date'),
        blank=True,
        null=True,
    )

    history = ExtraHistoricalRecords()

    class Meta:
        # Custom table is used, because these models were moved from an existing app.
        db_table = 'organizations_subscription'

    def __str__(self):
        return '{org} subscription'.format(org=self.organization.name)

    @property
    def is_trial_ended(self):
        if self.trial_end_date:
            return timezone.now() > self.trial_end_date
        return False

    def get_status_display(self):
        """
        Return the ``status`` to be presented to the user.

        Possible values:
        https://stripe.com/docs/api/python#subscription_object-status
        """
        return self.status.replace('_', ' ').title()

    def default_trial_end_date(self):
        """Date of trial period end."""
        if self.plan is not None:
            return (
                self.organization.pub_date + timedelta(days=self.plan.trial)
            )

    def save(self, *args, **kwargs):
        if self.trial_end_date is None:
            self.trial_end_date = self.default_trial_end_date()
        super().save(*args, **kwargs)
