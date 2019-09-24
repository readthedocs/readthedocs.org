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

The project privacy level is also used to serve the 404.html page,
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

The protected privacy level was meant to hid versions from listings and search.
For the community site these versions are treated like public versions,
and on the commercial site they are treated like private.

The protected privacy level is currently hidden.
To keep the behavior of hid the versions from listings and search,
a new field should be added to the Version model: ``hidden``.
The privacy level (public or private) would be respected to determinate access to the documentation.

For the community site, the privacy level would be public and can't be changed.

The default privacy level of new versions for the commercial site would be ``private``.

Footer
------

The footer is used to display not hidden versions that the current user has access to.

For the community site not changes are required on the footer.

For the commercial site we use the project level privacy to decide if show or not
links to the project's dashboard: downloads, project home, and builds.
Given that the project privacy level would be removed (and the dashboard is always under login),
those links would never be shown (except for admin users).

Migration
---------

To differentiate between allowing or not privacy levels,
we need to add a setting ``RTD_ALLOW_PRIVACY_LEVELS``.

For the community and commercial site, we need to:

- Remove/change code that depend on the project's privacy level.
  Use the default version's privacy level instead.

  - Display robots.txt
  - Serve 404.html page
  - Display sitemap.xml
  - Querysets

- Remove the project privacy level.
- Migrate all protected versions to have the attribute ``hidden = True``,
  and set their privacy level to public for the community site and private for the commercial site.
- Change all querysets used to list versions on the footer and on search to use the ``hidden`` attribute.
- Update docs

For the community site:

- Hide all privacy level related settings from the version form.
- Mark all versions as public.

For the commercial site:

- Always hide the dashboard
- Show links to the dashboard (downloads, builds, project home) on the footer only to admin users.
