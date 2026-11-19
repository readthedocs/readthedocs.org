Troubleshooting GitHub App integrations
=======================================

.. TODO all of these are more about connected repositories, not integrations. This
   should be troubleshooting information for project configuration _and_ creation.
   Move there.

For projects using a :doc:`../github-app` integration,
there may be some cases where either your repository is not listed or cannot be
selected as a connected repository.

These fixes are unique to our GitHub App integration, webhook integrations use a
different connection mechanism and cannot not be repaired in the same way as our
GitHub App integration.

Repository is not listed 
------------------------

When using our :doc:`GitHub App integration </projects/integrations/github-app>`,
the primary reason why a repository may not be listed in your repository list
is that the repository was not included in the GitHub App installation.

If this is an organization repository, you may also need to request approval
from your organization admins for our GitHub App.

You can try updating your GitHub App installation to include the repository

- `Read the Docs Community <https://github.com/apps/read-the-docs-community/installations/new/>`__
- `Read the Docs Business <https://github.com/apps/read-the-docs-business/installations/new/>`__

If you still can't see the repository in the list,
you can `force resynchronization of your repositories <Resynchronizing your repository list>`_
to update the repository information.

Repository can't be selected 
----------------------------

If the repository is listed in your list of repositories but can't be selected,
there are several potential issues:

* Your provider account does not have admin privileges on the repository.
* If your repository is part of a GitHub organization our GitHub App may not be
  approved by the organization yet. You can try requesting approval of our
  GitHub App from the organization. 
* You are trying to connect a private repository, which is only supported on |com_brand|.

If you update your repository permissions and still cannot select the repository,
you can `force resynchronization of your repositories <Resynchronizing your repository list>`_:

- `Read the Docs Community <https://app.readthedocs.org/dashboard/import/#repair>`__
- `Read the Docs Business <https://app.readthedocs.com/dashboard/import/#repair>`__

Resynchronizing your repository list
------------------------------------

If your repository list seems to be out of date,
try forcing a refresh of your repository list:

- `Read the Docs Community <https://app.readthedocs.org/dashboard/import/#repair>`__
- `Read the Docs Business <https://app.readthedocs.com/dashboard/import/#repair>`__
