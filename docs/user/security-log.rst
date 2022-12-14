Security Log
============

Security logs allow you to audit what has happened recently in your organization or account.
This feature is quite important for many security compliance programs,
as well as the general peace of mind of knowing what is happening on your account.
We store the IP address and the browser used on each event,
so that you can confirm this access was from the intended person.


.. _User-Agent: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/User-Agent

User security log
-----------------

We store user security logs for the last 90 days, and track the following events:

- Authentication on the dashboard
- Authentication on documentation pages (:doc:`/commercial/index` only)

Authentication failures and successes are both tracked.

To access your logs:

- Click on :guilabel:`<Username dropdown>`
- Click on :guilabel:`Settings`
- Click on :guilabel:`Security Log`

This log is useful to validate that no unauthorized logins have occured on your user account.

Organization security log
-------------------------

.. note::

   This feature exists only on :doc:`/commercial/index`.

The length of log store varies with your plan,
check our `pricing page <https://readthedocs.com/pricing/>`__ for more details.
We track the following events:

- Authentication on documentation pages from your organization
- User access to every documentation page from your organization (**Enterprise plans only**)

Authentication failures and successes are both tracked.

To access your organization logs:

- Click on :guilabel:`<Username dropdown>`
- Click on :guilabel:`Organizations`
- Click on :guilabel:`<Organization name>`
- Click on :guilabel:`Settings`
- Click on :guilabel:`Security Log`

Your organization security log is a great place to check periodically to ensure there hasn't been unauthorized access to your organization.

If you have any additional information that you wished the security log was capturing,
you can always reach out to :doc:`/support`.

.. seealso:: We have other security related information in our :doc:`/security` page.
