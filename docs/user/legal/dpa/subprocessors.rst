Sub-processor list
==================

:Effective: April 16, 2021
:Last updated: August 9, 2024

Read the Docs for Business uses services from the following sub-processors to
provide documentation hosting services. This document supplements :doc:`our Data
Processing Addendum <index>` and may be separately updated on a periodic basis.
A sub-processor is a third party data processor who has or potentially will have
access to or will process personal data.

.. seealso::
    Previous versions of this document, as well as the change history to this
    document, are available `on GitHub`_

.. _on GitHub: https://github.com/readthedocs/readthedocs.org/commits/main/docs/legal/dpa/subprocessors.rst

Infrastructure
--------------

Amazon Web Services, Inc.
    Cloud infrastructure provider.

Services
--------

Elasticsearch B.V.
    Hosted ElasticSearch services for documentation search. Search indexes do
    not include user data.

Sendgrid, Inc.
    Provides email delivery to dashboard and admin users for site notifications
    and other generated messages. The body of notification emails can include
    user information, including email address.

Plausible
    Website analytics for dashboard and Read the Docs owned documentation sites.

Stripe Inc.
    Subscription payment provider. Data collected can include user data necessary
    to process payment transactions, however this data is not processed directly
    by Read the Docs.

Monitoring
----------

New Relic
    Application performance analytics. Data collected can include
    user data and visitor data used within application code.

Sentry
    Error analytics service used to log and track application errors. Error
    reports can include arguments passed to application code, which can include
    user and visitor data.

Support
-------

FrontApp, Inc.
    Customer email support service. Can have access to user data, including user
    email and IP address, and stores communications related to user data.
