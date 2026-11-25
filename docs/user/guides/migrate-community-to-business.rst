How to migrate projects from Read the Docs Community to Business
================================================================

.. include:: /shared/admonition-rtd-business.rst

This guide walks you through moving your existing documentation from
|org_brand| (``app.readthedocs.org``) to |com_brand| (``app.readthedocs.com``),
where your projects live inside an :doc:`organization </commercial/organizations>`.

|org_brand| and |com_brand| are separate platforms that run on separate
infrastructure, with separate accounts and dashboards.
Because of this, **projects are not transferred automatically between them**.
Instead, you re-import each repository on |com_brand|.

Migrate a project
-----------------

#. Sign in to |com_brand| at https://app.readthedocs.com/ with an account
   that is an *owner* of your organization.
#. Connect your Git provider so Read the Docs can list your repositories.
   See :doc:`/guides/connecting-git-account`.
#. Import the repository as a new project, into your organization rather than
   a personal account. See :doc:`/intro/add-project`.
#. Repeat for each project you want to move.

.. tip::

   Keep your projects on |org_brand| in place until the new ones build
   successfully on |com_brand|. This lets you verify everything first.

Keep your URLs working
----------------------

When you move a project, its default URL changes from ``*.readthedocs.io``
to ``*.readthedocs-hosted.com``. You have two options to avoid broken links:

* **Move your custom domain.** If your documentation is served from your own
  domain, add it to the new project once it builds, then update your DNS.
  See :doc:`/guides/custom-domains`.
* **Add redirects.** If you don't use a custom domain, add redirects from the
  old paths to the new ones. See :doc:`/guides/redirects`.

Configure access
----------------

Decide how your team gets access to the projects in the organization:

* **Teams** — Grant admin or read-only access to specific projects.
  See :doc:`/guides/manage-read-the-docs-teams`.
* **Single sign-on** — Grant access based on the permissions people already
  have on your Git provider. See :doc:`/commercial/single-sign-on`.

Clean up
--------

Once the new projects build and your team has access, remove or
:doc:`mark as abandoned </abandoned-projects>` the old projects on
|org_brand| so they are no longer built or indexed.

.. note::

   We're happy to help with larger migrations. Reach out through
   :doc:`/support` and mention your organization name.
