How to manage organization owners and teams
============================================

.. include:: /shared/admonition-rtd-business.rst

Read the Docs uses teams within an organization to group users and provide permissions to projects.
This guide will cover how to manage both organization owners and team members.
You can read more about organizations and teams in our :doc:`/commercial/organizations` documentation.

Managing organization owners
-----------------------------

Organization owners have full administrative access to the organization and all its projects.
They can manage settings, teams, members, and other owners.

Adding an owner to an organization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To grant someone full administrative access to your organization, add them as an owner.

Follow these steps:

1. Navigate to the `organization management page <https://app.readthedocs.com/organizations/choose/organization_detail/>`__.
2. Select your organization from the list.
3. In the right sidebar, locate the :guilabel:`Owners` section.
4. Click :guilabel:`Add` in the Owners section.
5. Enter the user's Read the Docs username or email address.
6. Click :guilabel:`Add owner`.

The user will receive an invitation and must accept it to become an owner.

Removing an owner from an organization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To revoke administrative access from an organization owner:

Follow these steps:

1. Navigate to the `organization management page <https://app.readthedocs.com/organizations/choose/organization_detail/>`__.
2. Select your organization from the list.
3. In the right sidebar, find the :guilabel:`Owners` section.
4. Click :guilabel:`Remove` next to the owner you want to remove.

.. note::

   You cannot remove the last owner from an organization.
   There must always be at least one owner.

Managing team members
---------------------

Adding a user to a team
~~~~~~~~~~~~~~~~~~~~~~~

Adding a user to a team gives them all the permissions available to that team,
whether it's *read-only* or *admin*.

Follow these steps:

1. Navigate to the `teams management page <https://app.readthedocs.com/organizations/choose/organization_team_list/>`__.
2. Click on a :guilabel:`<team name>`.
3. Click :guilabel:`Invite Member`.
4. Input the user's Read the Docs username or email address.
5. Click :guilabel:`Add member`.

Removing a user from a team
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Removing a user from a team removes all permissions that team gave them.

Follow these steps:

1. Navigate to the `teams management page <https://app.readthedocs.com/organizations/choose/organization_team_list/>`__.
2. Click on :guilabel:`<team name>`.
3. Click :guilabel:`Remove` next to the user.


Granting access to import a project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Make the user a member of any team with *admin* permissions,
they will be granted access to import a project on that team.

Automating team management
--------------------------

You can manage teams more easily using our :doc:`single sign-on </commercial/single-sign-on>` features.

.. seealso::

   :doc:`/commercial/organizations`
     General information about the *organizations* feature.
