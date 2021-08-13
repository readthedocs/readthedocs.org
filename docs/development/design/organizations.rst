Organizations
=============

Currently we don't support organizations in the community site
(a way to group different projects),
we only support individual accounts.

Several integrations that we support like GitHub and Bitbucket have organizations,
where users group their repositories and manage them in groups rather than individually.

Why move organizations in the community site?
---------------------------------------------

We support organizations in the commercial site,
having no organizations in the community site makes the code maintenance difficult for Read the Docs developers.
Having organizations in the community site will make the differences between both more easy to manage.

Users from the community site can have organizations in external sites from where we import their projects
(like GitHub, Gitlab).
Currently users have all projects from different organizations in their account.
Having not a clear way to group/separate those.

We are going to first move the code,
and after that enable the feature on the community site.

How are we going to support organizations?
------------------------------------------

Currently only users can own projects in the community site.
With organizations this is going to change to: 
Users and organizations can own projects.

With this, the migration process would be straightforward for the community site.

For the commercial site we are only to allow organizations to own projects for now
(since the we have only subscriptions per organizations).

What features of organizations are we going to support?
-------------------------------------------------------

We have the following features in the commercial site that we don't have on the community site:

- Owners
- Teams
- Permissions
- Subscriptions

Owners should be included to represent owners of the current organization.

Teams, this is also handy to manage access to different projects under the same organization.

Permissions,
currently we have two type of permissions for teams: admin and read only.
Read only permissions doesn't make sense in the community site since we only support public projects/versions
(we do support private versions now, but we are planning to remove those).
So, we should only support admin permissions for teams.

Subscriptions, this is only valid for the corporate site,
since we don't charge for use in the community site.

How to migrate current projects
-------------------------------

Since we are not replacing the current implementation,
we don't need to migrate current projects from the community site nor from the corporate site.

How to migrate the organizations app
------------------------------------

The migration can be split in:

#. Remove/simplify code from the organizations app on the corporate site.
#. Isolate/separate models and code that isn't going to be moved.
#. Start by moving the models, managers, and figure out how to handle migrations.
#. Move the rest of the code as needed.
#. Activate organizations app on the community site.
#. Integrate the code from the community site to the new code.
#. UI changes

We should start by removing unused features and dead code from the organizations in the corporate site,
and simplify existing code if possible (some of this was already done).

Isolate/separate the models to be moved from the ones that aren't going to be moved.
We should move the models that aren't going to me moved to another app.

- Plan
- PlanFeature
- Subscription

This app can be named *subscriptions*.
We can get around the table names and migrations by setting the explicitly the table name to ``organizations_<model>``,
and doing a fake migration.
Following suggestions in https://stackoverflow.com/questions/48860227/moving-multiple-models-from-one-django-app-to-another,
that way we avoid having any downtime during the migration and any inconvenient caused from renaming the tables manually.

Code related to subscriptions should be moved out from the organizations app.

After that, it should be easier to move the organizations *app* (or part of it)
to the community site (and no changes to table names would be required).

We start by moving the models.

- Organization
- OrganizationOwner
- Team
- TeamInvite
- TeamMember

Migrations aren't moved, since all current migrations depend on other models that aren't
going to be moved.
In the community site we run an initial migration,
for the corporate site we run a fake migration.
The migrations left from the commercial site can be removed after that.

For managers and querysets that depend on subscriptions,
we can use our pattern to make overridable classes (inheriting from ``SettingsOverrideObject``).

Templates, urls, views, forms, notifications, signals, tasks can be moved later
(we just need to make use of the models from the ``readthedocs.organizations`` module).

If we decide to integrate organizations in the community site,
we can add/move the UI elements and enable the app.

After the app is moved,
we can move more code that depends on organizations to the community site.

Namespace
---------

Currently we use the project's slug as namespace,
in the commercial site we use the combination of ``organization.slug`` + ``project.slug`` as namespace,
since in the corporate site we don't care so much about a unique namespace between all users,
but a unique namespace per organization.

For the community site probably this approach isn't the best,
since we always serve docs publicly from ``slug.readthedocs.io``.
And most of the users don't have a custom domain.

The corporate site will use ``organization.slug`` + ``project.slug`` as slug,
And the community site will always use ``project.slug`` as slug, even if the project belongs to an organization.

We need to refactor the way we get the namespace to be more easy to manage in both sites.

Future Changes
--------------

Changes that aren't needed immediately after the migration,
but that should be done:

- UI for organizations in the community site.
- Add new endpoints to the API (v3 only).
- Make the relationship between the models ``Organization`` and ``Project`` one to many
  (currently many to many).
