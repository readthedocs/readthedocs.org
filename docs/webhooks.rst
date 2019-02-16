Webhooks
========

The primary method that Read the Docs uses to detect changes to your
documentation and versions is through the use of *webhooks*. Webhooks are configured with
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

.. _webhook-creation:

Webhook Creation
----------------

If you have :doc:`connected your Read the Docs account </connected-accounts>` to GitHub, Bitbucket, or GitLab,
a webhook will be set up automatically for your repository. However, if your
project was not imported through a connected account, you may need to
manually configure a webhook for your project.

To manually set up a webhook, go to :guilabel:`Admin` > :guilabel:`Integrations` >  :guilabel:`Add integration`
dashboard page and select the integration type you'd like to add.
After you have added the integration, you'll see a link to information about the integration.

As an example, the URL pattern looks like this: *readthedocs.org/api/v2/webhook/<project-name>/<id>/*.

Use this URL when setting up a new webhook with your provider -- these steps vary depending on the provider:

.. _webhook-integration-github:

GitHub
~~~~~~

* Go to the :guilabel:`Settings` page for your project
* Click :guilabel:`Webhooks` > :guilabel:`Add webhook`
* For **Payload URL**, use the URL of the integration on Read the Docs,
  found on the project's :guilabel:`Admin` > :guilabel:`Integrations` page.
  You may need to prepend *https://* to the URL.
* For **Content type**, both *application/json* and
  *application/x-www-form-urlencoded* work
* Select **Let me select individual events**,
  and mark **Pushes**, **Branch or tag creation**, and **Branch or tag deletion** events
* Leave the **Secrets** field black
* Finish by clicking **Add webhook**

You can verify if the webhook is working at the bottom of the GitHub page under **Recent Deliveries**.
If you see a Response 200, then the webhook is correctly configured.
For a 403 error, it's likely that the Payload URL is incorrect.

.. note:: The webhook token, intended for the GitHub **Secret** field, is not yet implemented.

.. _webhook-integration-bitbucket:

Bitbucket
~~~~~~~~~

* Go to the :guilabel:`Settings` > :guilabel:`Webhooks` > :guilabel:`Add webhook` page for your project
* For **URL**, use the URL of the integration on Read the Docs,
  found on the :guilabel:`Admin` > :guilabel:`Integrations`  page
* Under **Triggers**, **Repository push** should be selected
* Finish by clicking **Save**

.. _webhook-integration-gitlab:

GitLab
~~~~~~

* Go to the :guilabel:`Settings` > :guilabel:`Integrations` page for your project
* For **URL**, use the URL of the integration on Read the Docs,
  found on the :guilabel:`Admin` > :guilabel:`Integrations`  page
* Leave the default **Push events** selected and mark **Tag push events** also
* Finish by clicking **Add Webhook**

.. _webhook-integration-generic:

Using the generic API integration
---------------------------------

For repositories that are not hosted with a supported provider, we also offer a
generic API endpoint for triggering project builds. Similar to webhook integrations,
this integration has a specific URL, which can be found on the project's **Integrations** dashboard page
(:guilabel:`Admin` > :guilabel:`Integrations`).

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
    The integration token found on the project's **Integrations** dashboard page
    (:guilabel:`Admin` > :guilabel:`Integrations`).

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

Troubleshooting
---------------

My project isn't automatically building
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If your project isn't automatically building, you can check your integration on
Read the Docs to see the payload sent to our servers. If there is no recent
activity on your Read the Docs project webhook integration, then it's likely
that your VCS provider is not configured correctly. If there is payload
information on your Read the Docs project, you might need to verify that your
versions are configured to build correctly.

Either way, it may help to either resync your webhook integration (see
`Resyncing webhooks`_ for information on this process), or set up an entirely
new webhook integration.

.. _webhook-github-services:

I was warned I shouldn't use GitHub Services
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Last year, GitHub announced that effective Jan 31st, 2019, GitHub Services will stop
working [1]_. This means GitHub will stop sending notifications to Read the Docs
for projects configured with the ``ReadTheDocs`` GitHub Service. If your project
has been configured on Read the Docs for a long time, you are most likely still
using this service to automatically build your project on Read the Docs.

In order for your project to continue automatically building, you will need to
configure your GitHub repository with a new webhook. You can use either a
connected GitHub account and a :ref:`GitHub webhook integration <webhook-integration-github>`
on your Read the Docs project, or you can use a
:ref:`generic webhook integration <webhook-integration-generic>` without a connected
account.

.. [1] https://developer.github.com/changes/2018-04-25-github-services-deprecation/

.. _webhook-deprecated-endpoints:

I was warned that my project won't automatically build after April 1st
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In addition to :ref:`no longer supporting GitHub Services <webhook-github-services>`,
we have decided to no longer support several other legacy incoming webhook
endpoints that were used before we introduced project webhook integrations. When
we introduced our webhook integrations, we added several features and improved
security for incoming webhooks and these features were not added to our leagcy
incoming webhooks. New projects have not been able to use our legacy incoming
webhooks since, however if you have a project that has been established for a
while, you may still be using these endpoints.

After March 1st, 2019, we will stop accepting incoming webhook notifications for
these legacy incoming webhooks. Your project will need to be reconfigured and
have a webhook integration configured, pointing to a new webhook with your VCS
provider.

In particular, the incoming webhook URLs that will be removed are:

* ``https://readthedocs.org/build``
* ``https://readthedocs.org/bitbucket``
* ``https://readthedocs.org/github`` (as noted :ref:`above <webhook-github-services>`)
* ``https://readthedocs.org/gitlab``

In order to establish a new project webhook integration, :ref:`follow
the directions for your VCS provider <webhook-creation>`
