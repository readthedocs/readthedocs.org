Creating a generic API integration
==================================

Projects using repositories that are not hosted with a supported provider can
use our :doc:`../webhook:Generic API webhook` integration.

To manually set up an integration for your project,
go to :guilabel:`Settings` > :guilabel:`Integrations` > :guilabel:`Add integration`.

The repository provider should be configured to use a webhook or similar request
to the webhook URL specified for the integration.

.. seealso::
   :ref:`Triggering builds using our API <api/v3:Build triggering>`
      It's also possible to trigger builds through our API,
      however with this method there will be no stored record of webhook requests.

Authentication
--------------

This integration will require either token or user authentication to work.

Token authentication can be configured using the token
found on the integration's detail page after it is created.
The token should be passed in as a request parameter,
either as form data or as part of JSON data input.

If instead an authenticated user is used to make this request,
a check will be performed to ensure the authenticated user is a maintainer of the project.

Parameters
----------

This integration URL endpoint accepts the following arguments during an HTTP POST:

branches
    The names of the branches to trigger builds for. This can either be an array
    of branch name strings, or just a single branch name string.

    Default: **latest**

token
    The integration token found on the project's **Integrations** dashboard page
    (:guilabel:`Settings` > :guilabel:`Integrations`).


default_branch
    This is the default branch of the repository
    (ie. the one checked out when cloning the repository without arguments)

    *Optional*

For example, to build the ``dev`` branch of project ``example-project``
using the integration token ``1234``:

.. tabs::

   .. code-tab:: bash

      $ curl \
          --data "branches=dev&token=1234&default_branch=main" \
          https://app.readthedocs.org/api/v2/webhook/example-project/1/

   .. code-tab:: python

      import requests

      URL = "https://app.readthedocs.org/api/v2/webhook/example-project/1/"
      TOKEN = "1234"
      response = requests.post(
          URL,
          data={"branches": "dev", "token": TOKEN, "default_branch": "main"},
      )
      print(response.json())

A command like the one above could be called from a cron job or from a `Git hook`_.

.. _Git hook: http://www.kernel.org/pub/software/scm/git/docs/githooks.html
