Organizations
=============

Currently we don't support organizations in the community site
(a way to group different projects),
we only support individual accounts.

Several integrations that we support have organizations,
where users group their repositories.

Why support organizations in the community site?
------------------------------------------------

We support organizations in the commercial site,
having no organizations in the community site makes the code maintenance difficult.
Having organizations in the community site will make the differences between both more easy to manage.

Users from the community site can have organizations in external sites from where we import their projects
(like GitHub, Gitlab).
Currently users have all projects from different organizations in their account.
Having not a clear way to group/separate those.

How are we going to support organizations?
------------------------------------------

Currently users can have several projects.
With organizations we have two paths:

#. Support users and organizations to own projects
#. Support only organizations to own projects

With 1, the migration process would be straightforward for the community site.
With 2, the migration process would be straightforward for the commercial site.

How to migrate current projects
-------------------------------

If we choose to go with the second option from :ref:`development/design/organizations:How are we going to support organizations?`
we'll need to define a migration plan,
like creating an organization for all current projects.

But, for whatever option we choose,
we'll need to move the models defined in the corporate site
to the community site.

We should start by removing unused features and dead code from the organizations in the corporate site.
After that, it should be more easy to move the organizations *app* (or part of it)
to the community site (and not changes in table names would be required).

Additionally, we are going to need to edit the current querysets, modify/add UI elements,
and add new endpoints to the API (v3 only).

What features of organizations are we going to support?
-------------------------------------------------------

We have this features present in the commercial site:

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
