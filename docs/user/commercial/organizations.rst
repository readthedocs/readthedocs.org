Organizations
-------------

.. include:: /shared/admonition-rtd-business.rst

In this article, we explain how the *organizations* feature allows you to manage access to your projects.
On |com_brand|, your account is linked to an *organization*.
Organizations allow you to define both individual and team permissions for your projects.

.. seealso::

   :doc:`/guides/manage-read-the-docs-teams`
     A step-by-step guide to managing teams.

Important objects
~~~~~~~~~~~~~~~~~

* **Owners** -- Get full access to both view and edit the organization and all projects
* **Members** -- Get access to a subset of the organization projects
* **Teams** -- Where you give members access to a set of projects.

The best way to think about this relationship is:

*Owners* will create *Teams* to assign permissions to all *Members*.

.. warning::

   Owners, Members, and Teams behave differently if you are using
   :ref:`sso_git_provider`.

Team types
~~~~~~~~~~

You can create two types of teams:

* **Admin** -- Team members have full access to administer the projects assigned to the team. Members are allowed to change all of the settings, set notifications, and perform any action under the :guilabel:`Admin` tab for each project.
* **Read Only** -- Team members are only able to read the documentation of each project, and not able to change anything about each project.

Example
~~~~~~~

ACME would set up *Owners* of their organization,
for example, Frank Roadrunner would be an owner.
He has full access to the organization and all projects.

Wile E. Coyote is a contractor,
and will just have access to the new project Road Builder.

Roadrunner would set up a *Team* called *Contractors*.
That team would have *Read Only* access to the *Road Builder* project.
Then he would add *Wile E. Coyote* to the team.
This would give him access to just this one project inside the organization.
