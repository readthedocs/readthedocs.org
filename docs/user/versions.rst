Versions
========

Read the Docs supports publishing multiple versions of your documentation.
This allows your users to read the exact documentation for the specific version of the project they are using.

Versioning is useful for many reasons, but a few common use cases are:

* Shipping API client libraries that release versions across time.
* Having a "stable" and "latest" branch so that users can see the current release and the upcoming changes.
* Having a private development branch and a public stable branch so that in development releases aren't accidentally seen by users until they are released.

Versions are Git tags and branches
----------------------------------

When you add a project to Read the Docs,
all Git tags and branches are created as **Inactive** and **Not Hidden** versions by default.
During initial setup, Read the Docs also creates a ``latest`` version
that points to the default branch defined in your Git repository (usually ``main``).
This version should always exist and is the default version for your project.

If your project has any tags or branches with a name following
`semantic versioning <https://semver.org/>`_ (with or without a ``v`` prefix),
we also create a ``stable`` version tracking your most recent release.
If you want a custom ``stable`` version,
create either a tag or branch in your project with that name.

.. note::
   If you have at least one tag,
   tags will take preference over branches when selecting the stable version.

When you have :doc:`/reference/git-integration` configured for your repository,
we will automatically build each version when you push a commit.

Version states
--------------

Each version of your documentation has a state that changes the visibility of it to other users.

**Active** or **Inactive**
  - **Active** docs are visible, and builds can be triggered for the documentation.
  - **Inactive** versions *have their documentation content deleted* and builds cannot be triggered.

**Hidden** or **Not hidden**
  - **Not hidden** docs are listed on the :term:`flyout menu` on the docs site
    and are shown in search results.
  - **Hidden** docs are not listed on the :term:`flyout menu` on the docs site
    and are not shown in search results.

  Hiding a version doesn't make it private,
  any user with a link to its docs can still see it.
  This is useful when:

  - You no longer support a version, but you don't want to remove its docs.
  - You have a work in progress version and don't want to publish its docs just yet.

  Hidden versions are listed as ``Disallow: /path/to/version/``
  in the default :doc:`/reference/robots` created by Read the Docs.

**Public** or **Private** (only available on :doc:`/commercial/index`)
  - **Public** versions are visible to everyone, and are browsable by unauthenticated users.
  - **Private** versions are available only to people who have permissions to see them.
    They will return a `404 Not Found` when visited by people without viewing permissions.
    If you want to share your docs temporarily, see :doc:`/commercial/sharing`.

    If you want unauthenticated people to be able to view the build page of your public versions,
    you'll need to the set the :doc:`privacy level of your project </commercial/privacy-level>` to public.

Version syncing
---------------

Versions are automatically synced when the following events happen:

* A commit is pushed to your Git repository and you have a :doc:`Git integration </reference/git-integration>` configured.
* A build for any of your version is triggered.

If you find that your versions are out of date,
triggering a build is the best approach to ensuring they are synced again.

Managing your versions
----------------------

When you activate a version,
a :doc:`build </builds>` will be triggered to automatically deploy your documentation.

When you deactivate a version,
all of the artifacts of your version will be deleted and a ``404 Not Found`` page will be served for it.

You can change the state for each version of your documentation in the :guilabel:`Versions` tab of your project.

Version URL identifier (slug)
-----------------------------

Each version of your project has a unique URL identifier (slug).
This identifier is used to reference the version in your documentation, :term:`dashboard`, and :doc:`API </api/index>`.

A version slug is automatically generated from the name of the branch or tag in your repository,
some special characters like spaces and ``/`` are replaced with a dash (``-``), and the name is lowercased.
If the resulting slug collides with another one, a suffix is added (``_a``, ``_b``, etc.).

You can change the slug of a version in :ref:`the versions tab of your project <versions:Managing your versions>`,
but you should take the following into account:

- Changing the slug of an active version will result on its previous documentation being deleted, and a new build being triggered.
  Be careful when renaming active versions, specially old ones that might not build anymore.
- Any URL referencing your version with the old slug will return a ``404 Not Found`` page.
  You can use :ref:`an exact redirect <user-defined-redirects:Redirecting an old version to a new one>` to redirect users to the new URL,
- You may still see the original name of the version in some places,
  as changing the slug only affects the URL used in your documentation and how the APIs identify that version.
  `We are considering adding another field to be used for display in the future <https://github.com/readthedocs/readthedocs.org/issues/11979>`__.
- Sorting of versions in the version selector is done based on the slug,
  changing the slug of a version may change the order in which they are shown to your users.
  `We are considering adding another field to be used for sorting in the future <https://github.com/readthedocs/readthedocs.org/issues/11979>`__.
- You can't change the slug of versions that are managed by Read the Docs, like ``latest`` and ``stable``.
- Slugs must be unique for each version of your project.
- The slug can contain lowercase letters, numbers, dashes (``-``), underscores (``_``) and dots (``.``).
  If you try to use a slug that contains any other character, you'll get an error message with a suggestion of a valid slug.

.. warning::

   Changing the slug of an active version will result on its previous documentation being deleted, and a new build being triggered.
   Be careful when renaming active versions, specially old ones that might not build anymore.

Disabling versioning completely
-------------------------------

You can :doc:`configure a single version project </versioning-schemes>`,
and the version will be hidden from the URL.

Version warning notifications
-----------------------------

As part of :doc:`addons`, Read the Docs displays notifications in the following situations:

Non-stable notification
    A notification on all non-stable versions is shown to clearly communicate to readers they may be reading an outdated version of the documentation.

    Specifically, when a version is being shown that is not the ``stable`` version, and there is a ``stable``
    version available.

Latest version notification
    A notification shown on the latest version tells readers they are reading the latest/development version of the documentation that may include features not yet deployed.

    Specifically, when the ``latest`` version is being shown, and there's also an active ``stable`` version that is not hidden.

Each of these notifications can be configured by project admins in :ref:`addons:Configuring Read the Docs Addons`.

Redirects on root URLs
----------------------

When a user hits the root URL for your documentation,
for example ``https://pip.readthedocs.io/``,
they will be redirected to the **Default version**.
This defaults to **latest**,
but another common configuration is setting it to your **stable** version.

Versioning workflows
--------------------

Read the Docs makes certain assumptions about your documentation version defaults,
all of which can be reconfigured if necessary:

- The ``latest`` version points to the most up to date development code.
  If you develop on a branch that is different than the default for your version control system,
  set the **Default Branch** to the branch you use.

- **Tags** are semantic versioning compatible (according to  `PEP 440`_) snapshots
  of your documentation. The most recent semantic tag maps to the ``stable`` version.

  Semantic versioning allows "normal" version numbers like ``1.4.2``, as
  well as pre-releases like this: ``2.0a1``. The ``stable`` version of your documentation never includes a pre-release.
  An optional ``v`` prefix like ``v1.4.2`` or ``v2.0a1`` is also allowed.

- Branches are assumed to be **long-lived branches**,
  This is most useful for **release branches**, which are maintained over time for a specific release.
  An example would be a ``2.1`` branch that is kept up to date with the latest ``2.1.x`` release.

.. _PEP 440: https://www.python.org/dev/peps/pep-0440/
