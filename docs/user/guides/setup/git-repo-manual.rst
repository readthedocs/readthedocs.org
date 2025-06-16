How to manually configure a Git repository integration
======================================================

In this guide,
you will find the steps to manually integrate your Read the Docs project with any Git provider using :term:`webhooks <webhook>`.
Manual integration is most useful for Git providers that we don't support with automatic configuration.
Automatic configuration is supported for |git_providers_and|.

Git repositories that are imported manually **do not** have the required setup to send back a **commit status**.
If you need this integration,
you have to :doc:`configure the repository automatically </reference/git-integration>`.

..
  The following references were supposed to go inside tabs, which is
  supported here:
  https://github.com/readthedocs/readthedocs.org/pull/9675/files#diff-3f9d42f7636de1c3a557a6c7aa047b0eb45790e30eef04eea9eaff08318b75ce

  But because of otherwise harmless warnings in ePub builds, we save this
  as something that we can fix later once we can ignore those warnings or
  sphinx-tabs or sphinx-design can avoid triggering the warning.

  Refs comment from @humitos:
  https://github.com/readthedocs/readthedocs.org/issues/9816#issuecomment-1369913128

.. _webhook-integration-github:
.. _webhook-integration-bitbucket:
.. _webhook-integration-gitlab:

Manual integration setup
------------------------

You need to configure your Git provider integration to call a webhook that alerts Read the Docs of changes.
Read the Docs will sync versions and build your documentation whenever a Git commit happens.

.. tabs::

   .. tab:: GitHub

      * Go to the :guilabel:`Settings` page for your **GitHub project**
      * Click :guilabel:`Webhooks` > :guilabel:`Add webhook`
      * For **Payload URL**, use the URL of the integration on your **Read the Docs project**,
        found on the project's :guilabel:`Admin` > :guilabel:`Integrations` page.
        You may need to prepend *https://* to the URL.
      * For **Content type**, both *application/json* and
        *application/x-www-form-urlencoded* work
      * Fill the **Secret** field with the value from the integration on Read the Docs
      * Select **Let me select individual events**,
        and mark **Branch or tag creation**, **Branch or tag deletion**, **Pull requests** and **Pushes** events
      * Ensure **Active** is enabled; it is by default
      * Finish by clicking **Add webhook**.  You may be prompted to enter your GitHub password to confirm your action.

      You can verify if the webhook is working at the bottom of the GitHub page under **Recent Deliveries**.
      If you see a Response 200, then the webhook is correctly configured.
      For a 403 error, it's likely that the Payload URL is incorrect.

   .. tab:: GitLab

      * Go to the :guilabel:`Settings` > :guilabel:`Webhooks` page for your GitLab project
      * For **URL**, use the URL of the integration on **Read the Docs project**,
        found on the :guilabel:`Admin` > :guilabel:`Integrations`  page
      * Fill the **Secret token** field with the value from the integration on Read the Docs
      * Leave the default **Push events** selected,
        additionally mark **Tag push events** and **Merge request events**.
      * Finish by clicking **Add Webhook**

   .. tab:: Bitbucket

      * Go to the :guilabel:`Settings` > :guilabel:`Webhooks` > :guilabel:`Add webhook` page for your project
      * For **URL**, use the URL of the integration on Read the Docs,
        found on the :guilabel:`Admin` > :guilabel:`Integrations`  page
      * Under **Triggers**, **Repository push** should be selected
      * Fill the **Secret** field with the value from the integration on Read the Docs
      * Finish by clicking **Save**

   .. tab:: Gitea

      These instructions apply to any Gitea instance.

      .. warning::

         This isn't officially supported, but using the "GitHub webhook" is an effective workaround,
         because Gitea uses the same payload as GitHub. The generic webhook is not compatible with Gitea.
         See `issue #8364`_ for more details. Official support may be implemented in the future.

      On Read the Docs:

      * Manually create a "GitHub webhook" integration
        (this will show a warning about the webhook not being correctly set up,
        that will go away when the webhook is configured in Gitea)

      On your Gitea instance:

      * Go to the :guilabel:`Settings` > :guilabel:`Webhooks` page for your project on your Gitea instance
      * Create a new webhook of type "Gitea"
      * For **URL**, use the URL of the integration on Read the Docs,
        found on the :guilabel:`Admin` > :guilabel:`Integrations` page
      * Leave the default **HTTP Method** as POST
      * For **Content type**, both *application/json* and
        *application/x-www-form-urlencoded* work
      * Fill the **Secret** field with the value from the integration on Read the Docs
      * Select **Choose events**,
        and mark **Branch or tag creation**, **Branch or tag deletion** and **Push** events
      * Ensure **Active** is enabled; it is by default
      * Finish by clicking **Add Webhook**
      * Test the webhook with :guilabel:`Delivery test`

      Finally, on Read the Docs, check that the warnings have disappeared
      and the delivery test triggered a build.

      .. _issue #8364: https://github.com/readthedocs/readthedocs.org/issues/8364

   .. tab:: Others

      Other providers are supported through a generic webhook, see :ref:`webhook-integration-generic`.

Payload validation
------------------

All integrations are created with a secret token,
this offers a way to verify that a webhook request is legitimate.

This validation is done according to each provider:

- `GitHub <https://developer.github.com/webhooks/securing/>`__
- `GitLab <https://docs.gitlab.com/ee/user/project/integrations/webhooks.html#validate-payloads-by-using-a-secret-token>`__
- `Bitbucket <https://support.atlassian.com/bitbucket-cloud/docs/manage-webhooks/#Secure-webhooks>`__


Managing Integrations
---------------------

To manually set up an integration, go to :guilabel:`Admin` > :guilabel:`Integrations` >  :guilabel:`Add integration`
dashboard page and select the integration type you'd like to add.

As an example, the URL pattern looks like this: ``https://app.readthedocs.org/api/v2/webhook/<project-name>/<id>/*``.
Use this URL when setting up a new integration with your provider.

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
^^^^^^^^^^

This endpoint accepts the following arguments during an HTTP POST:

branches
    The names of the branches to trigger builds for. This can either be an array
    of branch name strings, or just a single branch name string.

    Default: **latest**

token
    The integration token found on the project's **Integrations** dashboard page
    (:guilabel:`Admin` > :guilabel:`Integrations`).


default_branch
    This is the default branch of the repository
    (ie. the one checked out when cloning the repository without arguments)

    *Optional*

For example, the cURL command to build the ``dev`` branch, using the token
``1234``, would be::

    curl -X POST -d "branches=dev" -d "token=1234" -d "default_branch=main"
    https://app.readthedocs.org/api/v2/webhook/example-project/1/

A command like the one above could be called from a cron job or from a `Git hook`_.

.. _Git hook: http://www.kernel.org/pub/software/scm/git/docs/githooks.html

Authentication
^^^^^^^^^^^^^^

This endpoint requires authentication. If authenticating with an integration
token, a check will determine if the token is valid and matches the given
project. If instead an authenticated user is used to make this request, a check
will be performed to ensure the authenticated user is an owner of the project.

Troubleshooting Git provider webhooks
-------------------------------------

Debugging webhooks
^^^^^^^^^^^^^^^^^^

If you are experiencing problems with an existing webhook, you may be able to
use the integration detail page to help debug the issue. Each project
integration, such as a webhook or the generic API endpoint, stores the HTTP
exchange that takes place between Read the Docs and the external source. You'll
find a list of these exchanges in any of the integration detail pages.

Webhook activation failed. Make sure you have the necessary permissions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you find this error,
make sure your user has permissions over the repository.
In case of GitHub,
check that you have granted access to the Read the Docs `OAuth App`_ to your organization.
A similar workflow is required for other supported providers.

.. _OAuth App: https://github.com/settings/applications


My project isn't automatically building
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If your project isn't automatically building, you can check your integration on
Read the Docs to see the payload sent to our servers. If there is no recent
activity on your Read the Docs project webhook integration, then it's likely
that your Git provider is not configured correctly. If there is payload
information on your Read the Docs project, you might need to verify that your
versions are configured to build correctly.
