Security logs
=============

Security logs allow you to audit what has happened recently in your organization or account.
This feature is quite important for many security compliance programs,
as well as the general peace of mind of knowing what is happening on your account.
We store the IP address and the browser used on each event,
so that you can confirm this access was from the intended person.

Security logs are only visible to organization owners.
You can invite other team members as owners.

.. seealso::

   :doc:`/legal/security-policy`
     General information and reference about how security is handled on Read the Docs.

User security log
-----------------

We store a user security log for the latest 90 days of activity.
This log is useful to validate that no unauthorized events have occurred.

The security log tracks the following events:

- Authentication on the dashboard.
- Authentication on documentation pages (:doc:`/commercial/index` only).
- When invitations to manage a project are sent, accepted, revoked or declined.

Authentication failures and successes are both tracked.

Logs are available in :menuselection:`<Username dropdown> --> Settings --> Security Log`.

Organization security log
-------------------------

.. include:: /shared/admonition-rtd-business.rst

The length of log storage varies with your plan,
check our `pricing page <https://about.readthedocs.com/pricing/>`__ for more details.
Your organization security log is a great place to check periodically to ensure there hasn't been unauthorized access to your organization.

Organization logs track the following events:

- Authentication on documentation pages from your organization.
- User accesses a documentation page from your organization (**Enterprise plans only**).
- User accesses a documentation's downloadable formats (**Enterprise plans only**).
- Invitations to organization teams are sent, revoked or accepted.

Authentication failures and successes are both tracked.

Logs are available in :menuselection:`<Username dropdown> --> Organizations --> <Organization name> --> Settings --> Security Log`.

If you have any additional information that you wished the security log was capturing,
you can always reach out to :doc:`/support`.

.. seealso::

    :doc:`/security`
      Security information related to our own platform, personal data treatment, and how to report a security issue.
