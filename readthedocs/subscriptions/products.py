"""
Read the Docs products.

This module contains the dataclasses that represent the products available.
The available products are defined in the ``RTD_PRODUCTS`` setting.
"""

import copy
from dataclasses import dataclass

from django.conf import settings

from readthedocs.subscriptions.constants import FEATURE_TYPES


@dataclass(slots=True)
class RTDProductFeature:
    # readthedocs.subscriptions.constants.TYPE_*
    type: str
    # Depending on the feature type, this number can represent a numeric limit, number of days, etc.
    value: int = 0
    # If this feature is unlimited for this product.
    unlimited: bool = False
    description: str = ""

    def get_description(self):
        if self.description:
            return self.description
        default_description = dict(FEATURE_TYPES).get(self.type)
        if self.unlimited:
            return f"{default_description} (unlimited)"
        if self.value:
            return f"{default_description} ({self.value})"
        return default_description

    def to_item(self):
        """
        Return a tuple with the feature type and the feature itself.

        Useful to use it as a dictionary item.
        """
        return self.type, self

    def __add__(self, other: "RTDProductFeature"):
        """Add the values of two features."""
        if self.type != other.type:
            raise ValueError("Cannot add features of different types")
        new_feature = copy.copy(self)
        if self.unlimited or other.unlimited:
            new_feature.unlimited = True
        else:
            new_feature.value = self.value + other.value
        return new_feature

    def __mul__(self, value: int):
        """Multiply the value of a feature by a number."""
        new_feature = copy.copy(self)
        if self.unlimited:
            return new_feature
        new_feature.value = self.value * value
        return new_feature


@dataclass(slots=True)
class RTDProduct:
    """A local representation of a Stripe product."""

    stripe_id: str
    features: dict[str, RTDProductFeature]
    # If this product should be available to users to purchase.
    listed: bool = False
    # If this product is an extra that can be added to a main plan.
    # For example, an extra builder.
    extra: bool = False

    def to_item(self):
        """
        Return a tuple with the stripe_id and the product itself.

        Useful to use it as a dictionary item.
        """
        return self.stripe_id, self


def get_product(stripe_id) -> RTDProduct:
    """Return the product with the given stripe_id."""
    return settings.RTD_PRODUCTS.get(stripe_id)


def get_listed_products():
    """Return a list of products that are available to users to purchase."""
    return [product for product in settings.RTD_PRODUCTS.values() if product.listed]


def get_products_with_feature(feature_type) -> list[RTDProduct]:
    """Return a list of products that have the given feature."""
    return [
        product for product in settings.RTD_PRODUCTS.values() if feature_type in product.features
    ]


def get_feature(obj, feature_type) -> RTDProductFeature:
    """
    Get the feature object for the given type of the object.

    If the object doesn't have the feature, return the default feature or None.

    :param obj: An organization or project instance.
    :param type: The type of the feature (readthedocs.subscriptions.constants.TYPE_*).
    """
    # Hit the DB only if subscriptions and organizations are enabled.
    if not settings.RTD_PRODUCTS or not settings.RTD_ALLOW_ORGANIZATIONS:
        return settings.RTD_DEFAULT_FEATURES.get(feature_type)

    from readthedocs.organizations.models import Organization
    from readthedocs.projects.models import Project

    if isinstance(obj, Project):
        # Fetch the subscription as well, as it's used just below.
        organization = obj.organizations.select_related("stripe_subscription").first()
    elif isinstance(obj, Organization):
        organization = obj
    else:
        raise TypeError

    # This happens when running tests on .com only.
    # In production projects are always associated with an organization.
    if not organization:
        return settings.RTD_DEFAULT_FEATURES.get(feature_type)

    # A subscription can have multiple products, but we only want
    # the products from the organization that has the feature we are looking for.
    available_stripe_products_id = [
        product.stripe_id for product in get_products_with_feature(feature_type)
    ]
    stripe_subscription = organization.stripe_subscription
    if stripe_subscription:
        subscription_items = stripe_subscription.items.filter(
            price__product__id__in=available_stripe_products_id
        ).select_related("price__product")
        final_rtd_feature = None
        for subscription_item in subscription_items:
            rtd_feature = settings.RTD_PRODUCTS[subscription_item.price.product.id].features[
                feature_type
            ]
            if final_rtd_feature is None:
                final_rtd_feature = rtd_feature * subscription_item.quantity
            else:
                final_rtd_feature += rtd_feature * subscription_item.quantity
        if final_rtd_feature:
            return final_rtd_feature

    # Fallback to the default feature if the organization
    # doesn't have a subscription with the feature.
    return settings.RTD_DEFAULT_FEATURES.get(feature_type)
