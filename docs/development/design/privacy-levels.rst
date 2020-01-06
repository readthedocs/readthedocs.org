Privacy Levels
==============

This document describes how to handle and unify privacy levels
on the community and commercial version of Read the Docs.

Current state
-------------

Currently, we have three privacy levels for projects and versions:

#. Public
#. Private
#. Protected (currently hidden)

These levels of privacy aren't clear and bring confusion to our users.
Also, the private level doesn't makes sense on the community site,
since we only support public projects.

Places where we use the privacy levels are:

- On serving docs
- Footer
- Dashboard

Project level privacy
---------------------

Project level privacy was meant to control the dashboard visibility.

This privacy level brings to confusion when users want to make a version public.
We should remove all the project privacy levels.

For the community site the dashboard would be always visible,
and for the commercial site, the dashboard would be always hidden.

The project privacy level is also used to serve the ``404.html`` page,
show ``robots.txt``, and show  ``sitemap.xml``.
The privacy level of the default version should be used instead.

Some other ideas about keeping the privacy level is to dictate the default version level of new versions,
but removing all other logic related to this privacy level.
This can be (or is going to be) possible with automation rules,
so we can just remove the field.

Version level privacy
---------------------

Version level privacy is mainly used to restrict access to documentation.
For public level, everyone can access to the documentation.
For private level, only users that are maintainers or that belong to a team with access
(for the commercial site)
can access to the documentation.

The protected privacy level was meant to hide versions from listings and search.
For the community site these versions are treated like public versions,
and on the commercial site they are treated like private.

The protected privacy level is currently hidden.
To keep the behavior of hiding versions from listings and search,
a new field should be added to the Version model and forms: ``hidden`` (`#5321 <https://github.com/readthedocs/readthedocs.org/issues/5321>`__).
The privacy level (public or private) would be respected to determine access to the documentation.

For the community site, the privacy level would be public and can't be changed.

The default privacy level of new versions for the commercial site would be ``private``
(this is the ``DEFAULT_PRIVACY_LEVEL`` setting).

Footer
------

The footer is used to display not hidden versions that the current user has access to.

For the community site no changes are required on the footer.

For the commercial site we use the project level privacy to decide if show or not
links to the project's dashboard: downloads, project home, and builds.
Given that the project privacy level would be removed (and the dashboard is always under login),
those links would never be shown, except for admin users (owners or from a team with admin access)
since they are the only ones allowed to make changes on the project.

Overview
--------

For the community site:

- The project's dashboard is visible to all users.
- All versions are always public.
- The footer shows links to the project's dashboard (build, downloads, home) to all users.
- Only versions with ``hidden = False`` are listed on the footer and appear on search results.
- If a project has a `404.html` file on the default version, it's served.
- If a project has a ``robots.txt`` file on the default version, it's served.
- A ``sitemap.xml`` file is always served.

For the commercial site:

- The project's dashboard is visible to only users that have read permission over the project.
- The footer shows links to the project's dashboard (build, downloads, home) to only admin users.
- Only versions with ``hidden = False`` are listed on the footer and appear on search results.
- If a project has a `404.html` file on the default version, it's served if the user has permission over that version.
- If a project has a ``robots.txt`` file on the default version, and it's public, it's served.
- A ``sitemap.xml`` file is served if the user has at least on public version.
  And it will only list public versions.

Migration
---------

To differentiate between allowing or not privacy levels,
we need to add a setting ``RTD_ALLOW_PRIVACY_LEVELS`` (``False`` by default).

For the community and commercial site, we need to:

- Remove/change code that depends on the project's privacy level.
  Use the global setting ``RTD_ALLOW_PRIVACY_LEVELS`` and default version's privacy level instead.

  - Display robots.txt
  - Serve 404.html page
  - Display sitemap.xml
  - Querysets

- Remove `Project.privacy_level` field
- Migrate all protected versions to have the attribute ``hidden = True`` (data migration),
  and set their privacy level to public for the community site and private for the commercial site.
- Change all querysets used to list versions on the footer and on search to use the ``hidden`` attribute.
- Update docs

For the community site:

- Hide all privacy level related settings from the version form.
- Don't expose privacy levels on API v3.
- Mark all versions as public.

For the commercial site:

- Always hide the dashboard
- Show links to the dashboard (downloads, builds, project home) on the footer only to admin users.

Upgrade path overview
---------------------

Community site
##############

The default privacy level for the community site is public for versions and the dashboard is always public.

Public project (community)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- Public version:
  Normal use case, no changes required.
- Protected version:
  Users didn't want to list this version on the footer,
  but also not deactivate it.
  We can do a data migration of those versions to the new ``hidden`` setting and make them public.
- Private version:
  Users didn't want to show this version to their users yet or they were testing something.
  This can be solved with the pull request builder feature and the ``hidden`` setting.
  We migrate those to public with the ``hidden`` setting.
  If we are worried about leaking anything from the version, we can email users before doing the change. 

Protected project (community)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Protected projects are not listed publicly.
Probably users were hosting a WIP project,
or personal public project.
A public project should work for them,
as we are removing listing all projects publicly (except for search).

The migration path for versions of protected projects is the same as a public project.

Private project (community)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Probably these users want to use our enterprise solution instead.
Or they were hosting a personal project.

The migration path for versions of private projects is the same as a public project.

If we are worried about leaking anything from the dashboard or build page,
we can email users before doing the change.

Commercial site
###############

The default privacy level for the commercial site is private for versions and the dashboard is show only to admin users.

Private project (commercial)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Private version:
  Normal usa case, not changes required.
- Protected version:
  Users didn't want to list this version on the footer,
  but also not deactivate it. This can be solved by using the new ``hidden`` setting.
  We can do a data migration of those versions to the new ``hidden`` setting and make them private.
- Public version:
  User has private code, but want to make public their docs.
  No changes required.

Protected project (commercial)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

I can't think of a use case for protected projects,
since they aren't listed publicly on the commercial site.

The migration path for versions of protected projects is the same as a private project.

Public project (commercial)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Currently we show links back to project dashboard if the project is public,
which probably users shouldn't see.
With the implementation of this design doc,
public versions don't have links to the project dashboard (except for admin users) and the dashboard is always under login.

- Private versions:
  Users under the organization can see links to the dashboard.
  Not changes required.
- Protected versions:
  Users under the organization can see links to the dashboard.
  We can do a data migration of those versions to the new ``hidden`` setting and make them private.
- Public versions:
  All users can see links to the dashboard.
  Probably they have an open source project,
  but they still want to manage access using the same teams of the organization.
  Not changes are required.

A breaking change here is:
users outside the organization would not be able to see the dashboard of the project.
