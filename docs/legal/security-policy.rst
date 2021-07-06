Security Policy
===============

Read the Docs adheres to the following security policies and procedures with
regards to development, operations, and managing infrastructure. You can also
find information on how we handle specific user data in our
:doc:`/privacy-policy`.

Our engineering team monitors several sources for security threats and responds
accordingly to security threats and notifications.

* We monitor 3rd party software included in our application and in our
  infrastructure for security notifications. Any relevant security patches are
  applied and released immediately.
* We monitor our infrastructure providers for signs of attacks or abuse and will
  respond accordingly to threats.

Infrastructure
--------------

Read the Docs infrastructure is hosted on Amazon Web Services (AWS).  We also
use Cloudflare services to mitigate attacks and abuse.

.. seealso::
    * `AWS security policies`_
    * `Cloudflare privacy and security policies`_

.. _`AWS security policies`: https://aws.amazon.com/security/
.. _`Cloudflare privacy and security policies`: https://www.cloudflare.com/privacypolicy/

Data and data center
--------------------

All user data is stored in the USA in multi-tenant datastores in Amazon Web
Services data centers. Physical access to these data centers is secured with a
`variety of controls`_ to prevent unauthorized access.

.. _`variety of controls`: https://aws.amazon.com/compliance/data-center/controls/

Application
-----------

Encryption in transit
    All documentation, application dashboard, and API access is transmitted
    using SSL encryption. We do not support unencrypted requests, even for
    public project documentation hosting.

Temporary repository storage
    We do not store or cache user repository data, temporary storage is used for
    every project build on Read the Docs.

Authentication
    Read the Docs supports SSO with GitHub, GitLab, Bitbucket, and Google Workspaces
    (formerly G Suite).

Payment security
    We do not store or process any payment details. All payment information is
    stored with our payment provider, Stripe -- a PCI-certified level 1 payment
    provider.

Engineering and Operational Practices
-------------------------------------

Immutable infrastructure
    We don’t make live changes to production code or infrastructure. All changes
    to our application and our infrastructure go through the same code review
    process before being applied and released.

Continuous integration
    We are constantly testing changes to our application code and operational
    changes to our infrastructure.

Incident response
    Our engineering team is on a rotating on-call schedule to respond to
    security or availability incidents.
