Allow Slug Change on Versions
=============================

Currently we don't allow users to change this value.
We generate one for them automatically based on the ``verbose_name`` of the version
(branch name or tag name).

Users care a lot about URLs,
we use the slug to generate the URL of a version.
Sometimes the generated slug isn't what they expect.

We already modify slugs of some projects from the admin when requested,
this document describes the benefits of allowing users to do it by themselves and implementation details.

Advantages of changing the slug
-------------------------------

Users can have more control over their version's URLs.

Users can make their versions compatible with :PEP:`440`,
so they are sorted the way the user expects.

Current usage of slugs
----------------------

Slugs are used heavily in our code,
to identify a version from the API and to serve the version.
And the slugs are shown on the version selector of the footer.

Current workarrounds to change slug
-----------------------------------

We currently change the slug of some projects from the admin when requested.
This is prone to error, since we can introduce an invalid character in the new slug.

Users can rename their branches or tags,
this isn't always posible for already released versions,
and probably involves changing a lot of places outside the project.

Problems of changing the slug
-----------------------------

Existing URLs will break.
Although, users can create an exact redirect to fix this::

   /en/{ current_slug }/$rest -> /en/{ new-slug }/

Current online docs would be inaccessible for a time.
Old docs need to be removed,
that can cause the docs to be down for a short time (till the new build finish)
or for a long time (if the new build fails and the user needs to investigate the cause).
This is only relevant for versions that were created a time ago (new versions wouldn't have many readers yet).
This can be fixed by first building the new docs and removing the old docs only if the new build is successful.

Using another field as alias
----------------------------

Another way to get around this is by creating a new field as alias (as we do with subprojects).
This option requires a lot of changes in our querysets and code related to serve docs.

Another suggestion is to use the ``verbose_name`` of the version,
this is a problem since the verbose_name of the version isn't slugified
(it can create some problems in how we handle URLs),
and we use the ``verbose_name`` to show the *real* name of the version (branch name or tag).

Restrictions
------------

We need to check that the new slug is compatible with our current code.

We can't allow users to change the slug of machine created versions,
because those have a special meaning in our code (like ``stable`` and ``latest``).

We need to remove all assets related to the previous slug,
and rebuild them for the new slug.

Implementation
--------------

The slug field will be added in the form to edit a version,
the users is warned of the implications of changing the slug
(and suggest posible solutions, like creating a redirect).

The new slug should be checked/slugified to be compatible with our code.
A task to delete previous artifacts would be triggered,
and a build build would be triggered for the new slug as well.
