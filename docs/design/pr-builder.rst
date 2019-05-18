Design of Pull Request Builder
==============================

Background
----------

This will focus on automatically building documentation for Pull Requests on Read the Docs projects.
This is one of the most requested feature of Read the Docs.
This document will serve as a design document for discussing how to implement this features.

Scope
-----

- Receiving ``pull_request`` webhook event from Github
- Fetching data from pull requests.
- Making Pull Requests work like temporary ``Version``
- Setting PR version Life time
- Excluding PR Versions from Elasticsearch Indexing
- Creating PR Versions when a pull request is opened and Triggering a build
- Triggering Builds on new PR commits
- Status reporting to Github
- Storing PR Version build Data
- Deleting PR version and the build data
- Excluding PR Versions from Search Engines
- Serving PR Docs
- Update the Footer API

Fetching Data from Pull Requests
--------------------------------

We already get Pull request events from Github webhooks.
We can utilize that to fetch data from pull requests.
when a ``pull_request`` event is triggered we can fetch the data of that pull request.
We can fetch the pull request by doing something similar to travis-ci.
ie: ``git fetch origin +refs/pull/<pr_number>/merge:``

Modeling Pull Requests as a Type of Version
-------------------------------------------

Pull requests can be Treated as a Type of Temporary ``Version``.
We might consider adding a Boolean Field or ``VERSION_TYPES`` to the ``Version`` model.

- If we go with Boolean Field we can add something like ``is_pull_request`` Field.
- If we go with ``VERSION_TYPES`` we can add something like ``pull_request`` alongside Tag and Branch.

We also have to update the current ``Version`` model ``QuerySet`` to exclude the PR versions.
We have to add ``QuerySet`` for PR versions also.

Excluding PR Versions from Elasticsearch Indexing
-------------------------------------------------

We should exclude to PR Versions from being Indexed to Elasticsearch.
We need to update the queryset to exclude PR Versions.

Creating Versions for Pull Requests
-----------------------------------

If the Github webhook event is ``pull_request`` and action is ``opened``,
it means a pull request was opened in the projects repository.
We can create a ``Version`` from the Payload data and trigger a initial build for the version.
A version will be created whenever RTD receives an event like this.

Triggering Build for New Commits in a Pull Request
--------------------------------------------------

We might want to trigger a new build for the PR version if there is a new commit on the PR.

Status Reporting to Github
--------------------------

We could send build status reports to Github. We could send if the build was Successful or Failed.
We can also send the build URL. By this we could show if the build passed or failed on Github something like travis-ci does.

As we already have the ``repo:status`` scope on our OAuth App,
we can send the status report to Github using the Github Status API.

Sending the status report would be something like this:

.. http:post:: /repos/:owner/:repo/statuses/:sha

.. code:: json

   {
       "state": "success",
       "target_url": "<pr_build_url>",
       "description": "The build succeeded!",
       "context": "continuous-documentation/read-the-docs"
   }

Storing Pull Request Docs
-------------------------

We need to think about how and where to store data after a PR Version build is finished.
We can store the data in a blob storage.

Deleting a PR Version
---------------------

We can delete a PR version when:

- A pull request is ``closed``. Github Webhook event (Action: ``closed``, Merged: ``False``)
- A pull request is ``merged``. Github Webhook event (Action: ``closed``, Merged: ``True``)
- A PR Version has reached its life time

We might want to set a life time of a PR version in case:

- We don't receive webhook event for a pull request being closed/merged
- If a PR is stale (not merged for a long time).

We need to delete the PR Version alongside the Build data from the blob storage.

Excluding PR Versions from Search Engines
-----------------------------------------

We should Exclude the PR Versions from Search Engines,
because it might cause problems for RTD users.
As users might land to a pull request doc but not the original Project Docs.
This will cause confusion for the users.

Serving PR Docs
---------------

We need to think about how we want to serve the PR Docs.

- We could serve the PR Docs from another Domain.
- We could serve the PR Docs using ``<pr_number>`` namespace on the same Domain.
  ``https://<project_slug>.readthedocs.io/en/pr/<pr_number>/``

Update the Footer API
---------------------

We need to update the Footer API to reflect the changes.
We might want to have a way to show that if this is a PR Build on the Footer.

- For PR Builds we might want to show a Visual hint. (The footer color might be Red).
- For regular project docs we should remove the PR Versions from the version list of the Footer.

Related Issues
--------------

- `Autobuild Docs for Pull Requests`_
- `Add travis-ci style pull request builder`_


.. _Autobuild Docs for Pull Requests: https://github.com/rtfd/readthedocs.org/issues/5684
.. _Add travis-ci style pull request builder: https://github.com/rtfd/readthedocs.org/issues/1340
