"""
Read the Docs products.

This module contains the dataclasses that represent the products available.
The available products are defined in the ``RTD_PRODUCTS`` setting.
"""
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
        return self.description or dict(FEATURE_TYPES).get(self.type)

    def to_item(self):
        """
        Return a tuple with the feature type and the feature itself.

        Useful to use it as a dictionary item.
        """
        return self.type, self


@dataclass(slots=True)
class RTDProduct:

    """A local representation of a Stripe product."""

    stripe_id: str
    features: dict[str, RTDProductFeature]
    # If this product should be available to users to purchase.
    listed: bool = False

    def to_item(self):
        """
        Return a tuple with the stripe_id and the product itself.

        Useful to use it as a dictionary item.
        """
        return self.stripe_id, self


def get_product(stripe_id):
    """Return the product with the given stripe_id."""
    return settings.RTD_PRODUCTS.get(stripe_id)


def get_listed_products():
    """Return a list of products that are available to users to purchase."""
    return [product for product in settings.RTD_PRODUCTS.values() if product.listed]


def get_products_with_feature(feature_type):
    """Return a list of products that have the given feature."""
    return [
        product
        for product in settings.RTD_PRODUCTS.values()
        if feature_type in product.features
    ]


def get_feature(obj, feature_type) -> RTDProductFeature:
    """
    Get the feature object for the given type of the object.

    If the object doesn't have the feature, return the default feature or None.

    :param obj: An organization or project instance.
    :param type: The type of the feature (readthedocs.subscriptions.constants.TYPE_*).
    """
    # Hit the DB only if subscriptions are enabled.
    if settings.RTD_PRODUCTS:
        from djstripe import models as djstripe

        from readthedocs.organizations.models import Organization
        from readthedocs.projects.models import Project

        if isinstance(obj, Project):
            organization = obj.organizations.first()
        elif isinstance(obj, Organization):
            organization = obj
        else:
            raise TypeError

        # A subscription can have multiple products, but we only want
        # the product from the organization that has the feature we are looking for.
        stripe_products_id = [
            product.stripe_id for product in get_products_with_feature(feature_type)
        ]
        stripe_product_id = (
            djstripe.Product.objects.filter(
                id__in=stripe_products_id,
                prices__subscription_items__subscription__rtd_organization=organization,
            ).values_list("id", flat=True)
            # TODO: maybe we should merge features from multiple products?
            .first()
        )
        if stripe_product_id is not None:
            return settings.RTD_PRODUCTS[stripe_product_id].features[feature_type]

    return settings.RTD_DEFAULT_FEATURES.get(feature_type)
