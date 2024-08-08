Versions
========

Read the Docs supports publishing multiple versions of your documentation
at the same time.
On initial import, we will create a ``latest`` version
that points to the default branch defined in your Git repository.

If your project has any tags or branches with a name following `semantic versioning <https://semver.org/>`_,
we also create a ``stable`` version tracking your most recent release.
If you want a custom ``stable`` version,
create either a tag or branch in your project with that name.

When you have :doc:`/integrations` configured for your repository,
we will automatically build each version when you push a commit.

Version states
--------------

Each version of your documentation has a combination of three states (**Active**, **Public**, and **Hidden**) which determine its visibility on your site:

You can change the states for each version of your documentation in the :guilabel:`Versions` tab of your project.

**Active** or **Inactive**
  - **Active** docs are visible, and builds can be triggered for the documentation.
  - Docs for **Inactive** versions *are deleted* and builds cannot be triggered.

**Hidden** or **Not hidden**
  - **Hidden** docs are not listed on the :term:`flyout menu` on the docs site,
    or shown in search results from another version on the docs site
    (like on search results from a superproject).
  - **Not hidden** docs are listed on the :term:`flyout menu` on the docs site,
    and are shown in search results on the docs site.

  Hiding a version doesn't make it private,
  any user with a link to its docs can still see it.
  This is useful when:

  - You no longer support a version, but you don't want to remove its docs.
  - You have a work in progress version and don't want to publish its docs just yet.

  Hidden verions are listed as ``Disallow: /path/to/version/``
  in the default `robots.txt file <https://www.robotstxt.org/>`__ created by Read the Docs.

**Public** or **Private** (only available on on :doc:`/commercial/index`)
  - Public versions are visible to everyone.
  - Private versions are available only to people who have permissions to see them.
    They will not display on any list view, and will 404 when visted by people without viewing permissions.
    If you want to share your docs temporarily, see :doc:`/commercial/sharing`.

    In addition, if you want other users to view the build page of your public versions,
    you'll need to the set the :doc:`privacy level of your project </commercial/privacy-level>` to public.

Tags and branches
-----------------

Read the Docs supports two workflows for versioning:

- based on tags
- based on branches

If you have at least one tag,
tags will take preference over branches when selecting the stable version.

Version warning
---------------

As part of the new :doc:`addons`, Read the Docs displays notifications in the following situations:

Non-stable notification
    A notification on all non-stable versions is shown to clearly communicate to readers they may be reading an outdated version of the documentation.

    Specifically, when a version is being shown that is not the ``stable`` version, and there is a ``stable``
    version available.

Latest version notification
    A notification shown on the latest version tells readers they are reading the latest/development version of the documentation that may include features not yet deployed.

    Specically, when the ``latest`` version is being shown, and there's also an active ``stable`` version that is not hidden.

Each of these notifcations can be configured by project admins in :ref:`addons:Configuring Read the Docs Addons`

.. note::

   An older version of these warning banners is only available to projects that had enabled it before the release of :doc:`addons`.

Redirects on root URLs
----------------------

When a user hits the root URL for your documentation,
for example ``https://pip.readthedocs.io/``,
they will be redirected to the **Default version**.
This defaults to **latest**,
but could also point to your latest released version.

Versioning workflows
--------------------

Read the Docs makes certain assumptions about your documentation version defaults,
all of which can be reconfigured if you need to:

- ``latest`` version points to the most up to date development code.
  If you develop on a branch that is different than the default for your version control system,
  set the **Default Branch** to the branch you use.

- **tags** are semantic versioning compatible (according to  `PEP 440`_) snapshots
  of your documentation. The most recent semantic tag maps to the ``stable`` tag.

  Semantic versioning allows "normal" version numbers like ``1.4.2``, as
  well as pre-releases like this: ``2.0a1``. The ``stable`` version of your documentation never includes a pre-release.

- If you have documentation changes on a **long-lived branch**,
  you can build those too, to see how the new docs will be built.
 This is most useful for **release branches**, which are maintained over time for a specific release. An example would be a ``2.1`` branch that is kept up to date with the latest ``2.1.x`` release. 

.. _PEP 440: https://www.python.org/dev/peps/pep-0440/
