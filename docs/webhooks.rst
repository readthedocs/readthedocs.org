Webhooks
========

The primary method that Read the Docs uses to detect changes to your
documentation is through the use of *webhooks*. Webhooks are configured with
your repository provider, such as GitHub, Bitbucket or GitLab, and with each commit,
merge, or other change to your repository, Read the Docs is notified. When we
receive a webhook notification, we determine if the change is related to an
active version for your project, and if it is, a build is triggered for that
version.

Webhook Integrations
--------------------

You'll find a list of configured webhook integrations on your project's admin
dashboard, under **Integrations**. You can select any of these integrations to
see the *integration detail page*. This page has additional configuration
details and a list of HTTP exchanges that have taken place for the integration.

You need this information for the URL, webhook, or Payload URL needed by the
repository provider such as GitHub, GitLab, or Bitbucket.

Webhook Creation
----------------

If you have :doc:`connected your Read the Docs account </connected-accounts>` to GitHub, Bitbucket, or GitLab,
a webhook will be set up automatically for your repository. However, if your
project was not imported through a connected account, you may need to
manually configure a webhook for your project.

To manually set up a webhook, click **Add integration** on your project's
**Integrations** Admin dashboard page and select the integration type you'd like
to add. After you have added the integration, you'll see a link to information about the integration.

As an example, the URL pattern looks like this: *readthedocs.org/api/v2/webhook/<project-name>/<id>/*.

Use this URL when setting up a new webhook with your provider -- these steps vary depending on the provider:

GitHub
~~~~~~

* Go to the **Settings** page for your project
* Click **Webhooks** and then **Add webhook**
* For **Payload URL**, use the URL of the integration on Read the Docs, found on
  the the project's **Integrations** Admin dashboard page
* For **Content type**, both *application/json* and
  *application/x-www-form-urlencoded* work
* Select **Just the push event**
* Finish by clicking **Add webhook**

You can verify if the webhook is working at the bottom of the GitHub page under **Recent Deliveries**. If you see a Response 200, then the webhook is correctly configured.
For a 403 error, it's likely that the Payload URL is incorrect.

.. note:: The webhook token, intended for the GitHub **Secret** field, is not yet implemented.

Bitbucket
~~~~~~~~~

* Go to the **Settings** page for your project
* Click **Webhooks** and then **Add webhook**
* For **URL**, use the URL of the integration on Read the Docs, found on the
  **Dashboard** > **Admin** > **Integrations** page
* Under **Triggers**, **Repository push** should be selected
* Finish by clicking **Save**

GitLab
~~~~~~

* Go to the **Settings** page for your project
* Click **Integrations**
* For **URL**, use the URL of the integration on Read the Docs, found on the
  **Dashboard** > **Admin** > **Integrations** page
* Leave the default **Push events** selected and mark **Tag push events** also
* Finish by clicking **Add Webhook**

Using the generic API integration
---------------------------------

For repositories that are not hosted with a supported provider, we also offer a
generic API endpoint for triggering project builds. Similar to webhook
integrations, this integration has a specific URL, found on the project's
**Integrations** Admin dashboard page on readthedocs.org.

Token authentication is required to use the generic endpoint, you will find this
token on the integration details page. The token should be passed in as a
request parameter, either as form data or as part of JSON data input.

Parameters
~~~~~~~~~~

This endpoint accepts the following arguments during an HTTP POST:

branches
    The names of the branches to trigger builds for. This can either be an array
    of branch name strings, or just a single branch name string.

    Default: **latest**

token
    The integration token. You'll find this value on the project's
    **Integrations** Admin dashboard page.

For example, the cURL command to build the ``dev`` branch, using the token
``1234``, would be::

    curl -X POST -d "branches=dev" -d "token=1234" https://readthedocs.org/api/v2/webhook/example-project/1/

A command like the one above could be called from a cron job or from a hook
inside Git_, Subversion_, Mercurial_, or Bazaar_.

.. _Git: http://www.kernel.org/pub/software/scm/git/docs/githooks.html
.. _Subversion: http://mikewest.org/2006/06/subversion-post-commit-hooks-101
.. _Mercurial: http://hgbook.red-bean.com/read/handling-repository-events-with-hooks.html
.. _Bazaar: http://wiki.bazaar.canonical.com/BzrHooks

Authentication
~~~~~~~~~~~~~~

This endpoint requires authentication. If authenticating with an integration
token, a check will determine if the token is valid and matches the given
project. If instead an authenticated user is used to make this request, a check
will be performed to ensure the authenticated user is an owner of the project.

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
