Organizations: permissions for projects and teams
-------------------------------------------------

.. include:: /shared/admonition-rtd-business.rst

In this article, we explain how the *organizations* feature on Read the Docs allows you to manage access to your projects.
On |com_brand|, your account is linked to an *organization*.
Organizations allow you to define both individual and team permissions for your projects.

In this article, we use ACME Corporation as our example organization.
ACME has a few people inside their organization,
some who need full access and some who just need access to one project.

.. seealso::

   :doc:`/guides/manage-read-the-docs-teams`
     A step-by-step guide to managing teams.

Member types
~~~~~~~~~~~~

* **Owners** -- Get full access to both view and edit the Organization and all Projects
* **Members** -- Get access to a subset of the Organization projects
* **Teams** -- Where you give members access to a set of projects.

The best way to think about this relationship is:

*Owners* will create *Teams* to assign permissions to all *Members*.

.. warning::

   Owners, Members and Teams behave differently if you are using
   :ref:`sso_git_provider`.

Team types
~~~~~~~~~~

You can create two types of Teams:

* **Admins** -- These teams have full access to administer the projects in the team. They are allowed to change all of the settings, set notifications, and perform any action under the **Admin** tab.
* **Read Only** -- These teams are only able to read and search inside the documents.

Example
~~~~~~~

ACME would set up *Owners* of their organization,
for example Frank Roadrunner would be an owner.
He has full access to the organization and all projects.

Wile E. Coyote is a contractor,
and will just have access to the new project Road Builder.

Roadrunner would set up a *Team* called *Contractors*.
That team would have *Read Only* access to the *Road Builder* project.
Then he would add *Wile E. Coyote* to the team.
This would give him access to just this one project inside the organization.
