Webhooks
========

The primary method that Read the Docs uses to detect changes to your
documentation is through the use of *webhooks*. Webhooks are configured with
your repository provider and with each commit, merge, or other change to your
repository, Read the Docs is notified. When this happens, we determine if the
change is related to an active version for your project, and if it is, a build
is triggered for that version.

Webhook creation
----------------

If you import a project using a connected account, a webhook will be set up
automatically for your repository. However, if your project was not imported
through a connected account, you may need to manually configure a webhook for
your project.

To manually set up a webhook, you must first create the corresponding
*integration* on your project's **Integrations** admin page. On this page, you
can click **Add integration** and select the integration type you'd like to add.
In order to set up a new webhook with your provider, you'll need the *webhook
URL*. You can get this URL by selecting the integration you just added on the
list of integrations.

The steps you need to take to manually set up a webhook vary depending on the
provider:

GitHub
~~~~~~

* Go to the **Settings** page for your project
* Click **Webhooks** and then **Add webhook**
* For **Payload URL**, use the URL of the integration on Read the Docs, found on
  the integration detail page
* For **Content type**, both *application/json* and
  *application/x-www-form-urlencoded* work
* Select **Just the push event**
* Finish by clicking **Add webhook**

.. note:: The webhook secret is not yet respected

Bitbucket
~~~~~~~~~

* Go to the **Settings** page for your project
* Click **Webhooks** and then **Add webhook**
* For **URL**, use the URL of the integration on Read the Docs, found on the
  integration detail page
* Under **Triggers**, **Repository push** should be selected
* Finish by clicking **Save**

GitLab
~~~~~~

* Go to the **Settings** page for your project
* Click **Integrations**
* For **URL**, use the URL of the integration on Read the Docs, found on the
  integration detail page
* Leave the default **Push events** selected
* Finish by clicking **Add Webhook**

Using the generic API integration
---------------------------------

For repositories that are not hosted with a supported provider, we also offer a
generic API endpoint for triggering project builds. Similar to webhook
integrations, this integration has a specific URL, found on the integration
detail page. This integration can either be added manually or may be created
automatically if you had previously set up a webhook with your provider
manually. A username and password are required to use this endpoint. The
username used to access this endpoint must have admin privileges for the
specified project.

Parameters
~~~~~~~~~~

This endpoint accepts the following arguments during an HTTP POST:

branches
    The names of the branches to trigger builds for. This can either be an array
    of branch name strings, or just a single branch name string.

    Default: **latest**

For example, to build the ``dev`` branch, an example cURL command would be::

    curl -X POST -u username -d "branches=dev" https://readthedocs.org/api/v2/webhook/example-project/1/

Authentication
~~~~~~~~~~~~~~

This endpoint requires authentication. An authorization check will determine if
the authenticated user has permission to build the specified project.
Currently, we support Basic Auth, using your username and password.

Executing cURL with a username and password specified is not recommended, the
following will prompt for your password::

      curl -X POST -u "$username" https://readthedocs.org/api/v2/webhook/example-project/1/

To execute this command from a cron job or a hook inside Git_, Subversion_,
Mercurial_, or Bazaar_, consider using a secure method of storing this login.

.. _Git: http://www.kernel.org/pub/software/scm/git/docs/githooks.html
.. _Subversion: http://mikewest.org/2006/06/subversion-post-commit-hooks-101
.. _Mercurial: http://hgbook.red-bean.com/read/handling-repository-events-with-hooks.html
.. _Bazaar: http://wiki.bazaar.canonical.com/BzrHooks

Debugging webhooks
------------------

If you are experiencing problems with an existing webhook, you may be able to
use the integration detail page to help debug the issue. Each project
integration, such as a webhook or the generic API endpoint, stores the HTTP
exchange that takes place between Read the Docs and the external source. You'll
find a list of these exchanges in any of the integration detail pages.

Resyncing webhooks
------------------

It might be necessary to re-establish a webhook if you are noticing problems.
To resync a webhook from Read the Docs, visit the integration detail page and
follow the directions for re-syncing your repository webhook.
