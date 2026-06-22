How to migrate projects from Read the Docs Community to Business
================================================================

.. include:: /shared/admonition-rtd-business.rst

This guide walks you through moving your existing documentation from
|org_brand| (``app.readthedocs.org``) to |com_brand| (``app.readthedocs.com``),
where your projects live inside an :doc:`organization </commercial/organizations>`.

This is a common move when you start a paid subscription and want to
bring documentation that already exists on the community platform,
including a main project with several :doc:`subprojects </subprojects>`,
under a single organization.

.. contents:: Contents
   :local:
   :depth: 1

Before you start
----------------

|org_brand| and |com_brand| are separate platforms that run on separate
infrastructure, with separate accounts and dashboards.
Because of this, **projects are not transferred automatically between them**.
Instead, you re-import each repository on |com_brand| and recreate the
structure you had before (subprojects, custom domains, and access).

A few things are worth deciding up front:

* **Which organization owns the projects.** All projects on |com_brand|
  belong to an organization. Import your projects into the organization you
  registered, rather than into a personal account, so that ownership and
  billing stay with the organization.
* **How people will sign in.** You can manage access with Read the Docs
  :doc:`teams </guides/manage-read-the-docs-teams>`, or connect your Git
  provider for :doc:`single sign-on </commercial/single-sign-on>` so access
  follows the permissions already set on your repositories.
* **Whether you use a custom domain.** If your documentation is served from
  your own domain, plan the cutover so readers experience no downtime
  (see :ref:`guides/migrate-community-to-business:Move your custom domain`).

.. tip::

   If you have several accounts (for example, a personal community account
   and an organization account on Business), connect the Git account that
   has access to your repositories to the user that will import the projects.
   See :doc:`/guides/connecting-git-account`.

Step 1: Set up your organization
--------------------------------

Sign in to |com_brand| at https://app.readthedocs.com/ with the account
that is an *owner* of your organization.

#. Confirm the organization exists and that the right people are owners.
#. Connect your Git provider (for example, GitLab) to your account so that
   Read the Docs can list the repositories you want to import.
   See :doc:`/guides/connecting-git-account`.

.. seealso::

   :doc:`/commercial/organizations`
      How owners, members, and teams work on |com_brand|.

Step 2: Import your main project
--------------------------------

Start with the project that everything else hangs off of (your main
documentation project).

#. Go to your :term:`dashboard` and click :guilabel:`Add project`.
#. Select the repository for your main project and follow the import steps.

See :doc:`/intro/add-project` for the full import process.

.. note::

   Keep the project on |org_brand| in place until the new project builds
   successfully on |com_brand| and you have moved any custom domain.
   This lets you verify everything before readers are affected.

Step 3: Import each product as a subproject
-------------------------------------------

Recreate your subproject layout so all of your product documentation is
available under the main project again.

#. Import each product's repository as its own project (as in Step 2).
#. Open the **main** project and go to
   :guilabel:`Admin` > :guilabel:`Subprojects`.
#. Add each product project as a subproject, setting the same *alias* you
   used before so the URLs stay consistent
   (for example, ``/projects/<alias>/``).

.. seealso::

   :doc:`/guides/subprojects`
      Step-by-step instructions for creating and managing subprojects.

   :doc:`/subprojects`
      How subprojects share a domain and a search index.

.. tip::

   On |com_brand| Pro plans and above you can customize or remove the
   ``/projects/`` prefix. See :doc:`/url-path-prefixes`.

Step 4: Move your custom domain
-------------------------------

If your documentation is served from your own domain (for example,
``docs.example.org``), you move it after the new project builds correctly.

#. Add the domain to the main project on |com_brand| under
   :guilabel:`Admin` > :guilabel:`Domains`.
#. Update the DNS record to point at the |com_brand| target
   (in the form ``<hash>.domains.readthedocs.com``).
#. Wait for the SSL certificate to be issued, then verify the site loads.

Because a domain can only point to one place at a time, the cutover happens
when you change the DNS record. Build and check the new project first to
keep downtime to a minimum.

.. seealso::

   :doc:`/guides/custom-domains`
      Full instructions, including DNS records and SSL certificates.

Step 5: Preserve old URLs with redirects
----------------------------------------

If you are *not* moving a custom domain, your documentation URLs change from
``*.readthedocs.io`` to ``*.readthedocs-hosted.com``. To keep existing links
and search-engine results working, add redirects from the old paths to the
new ones.

.. seealso::

   :doc:`/guides/redirects`
      How to add redirect rules to a project.

   :doc:`/user-defined-redirects`
      Reference and examples for the different redirect types.

Step 6: Configure access for your team
--------------------------------------

Decide how your colleagues get access to the projects in the organization:

* **Teams** — Create teams and add members to grant admin or read-only
  access to specific projects. See
  :doc:`/guides/manage-read-the-docs-teams`.
* **Single sign-on with your Git provider** — Grant access based on the
  permissions people already have on your GitLab repositories. See
  :doc:`/guides/setup-single-sign-on-github-gitlab-bitbucket`.

.. warning::

   Owners, members, and teams behave differently once you enable
   :ref:`Git provider SSO <sso_git_provider>`. Choose one access model for
   the organization before adding many people.

Step 7: Clean up
----------------

Once the new projects build, the domain has moved, and your team has access:

#. Verify each subproject and version builds and renders correctly.
#. Confirm search returns results across subprojects.
#. When you are confident the migration is complete, remove or
   :doc:`mark as abandoned </abandoned-projects>` the old projects on
   |org_brand| so they are not built or indexed anymore.

.. note::

   We're happy to help with larger migrations. If you'd like a hand mapping
   out the move, reach out through :doc:`/support` and mention your
   organization name.
