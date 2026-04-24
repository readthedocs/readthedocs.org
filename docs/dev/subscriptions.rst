Subscriptions
=============

Subscriptions are available on |com_brand|,
we make use of Stripe to handle the payments and subscriptions.
We use dj-stripe to handle the integration with Stripe.

Local testing
-------------

To test subscriptions locally, you need to have access to the Stripe account,
and define add the API key and webhook using the Django Admin.

- API key: https://dashboard.stripe.com/test/apikeys
- Webhook: https://dashboard.stripe.com/test/webhooks

To test the webhook locally, follow `the official guide from djstripe <https://dj-stripe.dev/2.9/usage/local_webhook_testing/>`_

If this is your first time setting up subscriptions, you will to re-sync djstripe with Stripe:

.. code-block:: bash

   inv docker.manage djstripe_sync_models

The subscription settings (``RTD_PRODUCTS``) already mapped to match the Stripe prices from the test mode.
To subscribe to any plan, you can use any `test card from Stripe <https://stripe.com/docs/testing>`__,
for example: ``4242 4242 4242 4242`` (use any future date and any value for the other fields).

Modeling
--------

Subscriptions are attached to an organization (customer),
and can have multiple products attached to it.
A product can have multiple prices, usually monthly and yearly.

When a user subscribes to a plan (product), they are subscribing to a price of a product,
for example, the monthly price of the "Basic plan" product.

A subscription has a "main" product (``RTDProduct(extra=False)``),
and can have several "extra" products (``RTDProduct(extra=True)``).
For example, an organization can have a subscription with a "Basic Plan" product, and an "Extra builder" product.

Each product is mapped to a set of features (``RTD_PRODUCTS``) that the user will have access to
(different prices of the same product have the same features).
If a subscription has multiple products, the features are multiplied by the quantity and added together.
For example, if a subscription has a "Basic Plan" product with a two concurrent builders,
and an "Extra builder" product with quantity three, the total number of concurrent builders the
organization has will be five.

Life cycle of a subscription
----------------------------

When a new organization is created, a stripe customer is created for that organization,
and this customer is subscribed to the trial product (``RTD_ORG_DEFAULT_STRIPE_SUBSCRIPTION_PRICE``).

After the trial period is over, the subscription is canceled,
and their organization is disabled.

During or after the trial a user can upgrade their subscription to a paid plan
(``RTDProduct(listed=True)``).

Custom products
---------------

We provide 3 paid plans that users can subscribe to: Basic, Advanced and Pro.
Additionally, we provide an Enterprise plan, this plan is customized for each customer,
and it's manually created by the RTD core team.

To create a custom plan, you need to create a new product in Stripe,
and add the product id to the ``RTD_PRODUCTS`` setting mapped to the features that the plan will provide.
After that, you can create a subscription for the organization with the custom product,
our application will automatically relate this new product to the organization.

Extra products
--------------

We have one extra product: Extra builder.

To create a new extra product, you need to create a new product in Stripe,
and add the product id to the ``RTD_PRODUCTS`` setting mapped to the features that the
extra product will provide, this product should have the ``extra`` attribute set to ``True``.

To subscribe an organization to an extra product,
you just need to add the product to its subscription with the desired quantity,
our application will automatically relate this new product to the organization.
