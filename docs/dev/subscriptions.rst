Subscriptions
=============

Subscriptions are available on |com_brand|,
we make use of Stripe to handle the payments and subscriptions.

Local testing
-------------

To test subscriptions locally, you need to have access to the Stripe account,
and define the following settings with the keys from Stripe test mode:

- ``STRIPE_SECRET``: https://dashboard.stripe.com/test/apikeys
- ``STRIPE_TEST_SECRET_KEY``: https://dashboard.stripe.com/test/apikeys
- ``DJSTRIPE_WEBHOOK_SECRET``: https://dashboard.stripe.com/test/webhooks

To test the webhook locally, you need to run your local instance with ngrok, for example:

.. code-block:: bash

   ngrok http 80
   inv docker.up --http-domain xxx.ngrok.io

If this is your first time setting up subscriptions, you will to re-sync djstripe with Stripe:

.. code-block:: bash

   inv docker.manage djstripe_sync_models

The subscription settings (``RTD_PRODUCTS``) already mapped to match the Stripe prices from the test mode.
To subscribe to any plan, you can use any `test card from Stripe <https://stripe.com/docs/testing>`__,
for example: ``4242 4242 4242 4242`` (use any future date and any value for the other fields).
