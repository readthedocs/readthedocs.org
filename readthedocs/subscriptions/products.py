from dataclasses import dataclass

from django.conf import settings

from readthedocs.subscriptions.constants import FEATURE_TYPES


@dataclass(slots=True)
class RTDProductFeature:
    type: str
    value: int = 0
    unlimited: bool = False

    @property
    def description(self):
        return dict(FEATURE_TYPES).get(self.type)

    def to_item(self):
        return (self.type, self)


@dataclass(slots=True)
class RTDProduct:
    stripe_id: str
    listed: bool
    features: dict[str, RTDProductFeature]

    def to_item(self):
        return (self.stripe_id, self)


def get_listed_products():
    return [product for product in settings.RTD_PRODUCTS.values() if product.listed]


def get_products_with_feature(feature):
    return [
        product
        for product in settings.RTD_PRODUCTS.values()
        if feature in product.features
    ]


def get_feature(obj, type) -> RTDProductFeature:
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
            product.stripe_id for product in get_products_with_feature(type)
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
            return settings.RTD_PRODUCTS[stripe_product_id].features[type]

    return settings.RTD_DEFAULT_FEATURES.get(type)
