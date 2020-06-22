Single Sign-On
==============

.. note::

   This feature only exists on `Read the Docs for Business <https://readthedocs.com/>`__.


Single Sign-On is supported on |com_brand| for Pro and Enterprise plans.
:abbr:`SSO (Single Sign-On)` will allow you to manage all the users' permissions directly on GitHub.

.. note::

   Currently, we only supports GitHub as Identity Provider.
   We plan to support GitLab and Bitbucket soon as well.

.. note::

   SSO is currently in **Beta**. We are enabling it only to customers that requested it via our support channel.
   If you would like to apply for the Beta, please `contact us <mailto:support@readthedocs.com>`_.


Member Types
------------

Owners
~~~~~~

Owners are those users who created the Organization when Sign Up,
or where added by another owner as an organization owner.

They have access to view and edit all the organization's setting.

.. note::

   They are *not granted full access* to all the projects imported under the organization.
   Project's permission are *completely* managed at GitHub.
   This is a noticeable difference when the organization does not have SSO enabled.


Members
~~~~~~~

Members are users that have read/admin access to at least one of the projects imported under the organization.

They will have **read access** to all the projects imported where they have at least "Read" access
under the GitHub's repository associated to the project imported.

They will have **admin access** to those projects where they have at least "Write" access on GitHub's repositories.

.. note::

   Users don't have to be invited to the Read the Docs' organization.
   Just by granting access at GitHub on the repository imported under Read the Docs,
   the user become part of the organization automatically.


Team Types
----------

When SSO is enabled in your organization, Teams disappear completely.
Read and Admin access to the projects are managed at GitHub, as mentioned in the previous section.


How it works
------------

When users hit your documentation page, they will be asked to login before granting access to the documentation.
Under the login form, they can choose to login with GitHub, which will automatically create them an account under Read the Docs.
Then, if the user has access to read that repository on GitHub, permissions will be granted and the user will see the documentation.

The account created for those users, will also give them access to the Read the Docs' dashboard.
There they can see all the projects they have access to and, for those projects they have "Write" access on GitHub,
they will be able to administrate them as well.
