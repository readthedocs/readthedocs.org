Interesting settings
====================

BUILD_MEMORY_LIMIT
------------------

The maximum memory allocated to the virtual machine.
If this limit is hit, build processes will be automatically killed.
Examples: '200m' for 200MB of total memory, or '2g' for 2GB of total memory.

BUILD_TIME_LIMIT
----------------

An integer representing the total allowed time limit (in seconds) of build processes.
This time limit affects the parent process to the virtual machine and will force a virtual machine
to die if a build is still running after the allotted time expires.

PRODUCTION_DOMAIN
------------------

This is the domain that is used by the main application dashboard (not documentation pages).

RTD_INTERSPHINX_URL
-------------------

This is the domain that is used to fetch the intersphinx inventory file.
If not set explicitly this is the ``PRODUCTION_DOMAIN``.

DEFAULT_PRIVACY_LEVEL
---------------------

What privacy projects default to having. Generally set to `public`. Also acts as a proxy setting for blocking certain historically insecure options, like serving generated artifacts directly from the media server.

PUBLIC_DOMAIN
-------------

A special domain for serving public documentation.
If set, public docs will be linked here instead of the `PRODUCTION_DOMAIN`.


PUBLIC_DOMAIN_USES_HTTPS
------------------------

If ``True`` and ``PUBLIC_DOMAIN`` is set, that domain will default to
serving public documentation over HTTPS. By default, documentation is
served over HTTP.


ALLOW_ADMIN
-----------

Whether to include `django.contrib.admin` in the URL's.


RTD_BUILD_MEDIA_STORAGE
-----------------------

Use this storage class to upload build artifacts to cloud storage (S3, Azure storage).
This should be a dotted path to the relevant class (eg. ``'path.to.MyBuildMediaStorage'``).
Your class should mixin :class:`readthedocs.builds.storage.BuildMediaStorageMixin`.

RTD_FILETREEDIFF_ALL
--------------------

Set to ``True`` to enable the file tree diff feature for all projects.


ELASTICSEARCH_DSL
-----------------

Default:

.. code-block:: python

   {
      'default': {
         'hosts': '127.0.0.1:9200'
      },
   }

Settings for elasticsearch connection.
This settings then pass to `elasticsearch-dsl-py.connections.configure`_


ES_INDEXES
----------

Default:

.. code-block:: python

   {
        'project': {
            'name': 'project_index',
            'settings': {'number_of_shards': 5,
                         'number_of_replicas': 0
                         }
        },
        'page': {
            'name': 'page_index',
            'settings': {
                'number_of_shards': 5,
                'number_of_replicas': 0,
            }
        },
    }

Define the elasticsearch name and settings of all the index separately.
The key is the type of index, like ``project`` or ``page`` and the value is another
dictionary containing ``name`` and ``settings``. Here the ``name`` is the index name
and the ``settings`` is used for configuring the particular index.


ES_TASK_CHUNK_SIZE
------------------

The maximum number of data send to each elasticsearch indexing celery task.
This has been used while running ``elasticsearch_reindex`` management command.


ES_PAGE_IGNORE_SIGNALS
----------------------

This settings is used to determine whether to index each page separately into elasticsearch.
If the setting is ``True``, each ``HTML`` page will not be indexed separately but will be
indexed by bulk indexing.


ELASTICSEARCH_DSL_AUTOSYNC
--------------------------

This setting is used for automatically indexing objects to elasticsearch.

.. _elasticsearch-dsl-py.connections.configure: https://elasticsearch-dsl.readthedocs.io/en/stable/configuration.html#multiple-clusters


Docker pass-through settings
----------------------------

If you run a Docker environment, it is possible to pass some secrets through to
the Docker containers from your host system. For security reasons, we do not
commit these secrets to our repository. Instead, we individually define these
settings for our local environments.

We recommend using `direnv`_ for storing local development secrets.

.. _direnv: https://direnv.net/

Allauth secrets
~~~~~~~~~~~~~~~

It is possible to set the Allauth application secrets for our supported
providers using the following environment variables:

.. envvar:: RTD_SOCIALACCOUNT_PROVIDERS_GITHUB_CLIENT_ID
.. envvar:: RTD_SOCIALACCOUNT_PROVIDERS_GITHUB_SECRET
.. envvar:: RTD_SOCIALACCOUNT_PROVIDERS_GITHUBAPP_CLIENT_ID
.. envvar:: RTD_SOCIALACCOUNT_PROVIDERS_GITHUBAPP_SECRET
.. envvar:: RTD_SOCIALACCOUNT_PROVIDERS_GITLAB_CLIENT_ID
.. envvar:: RTD_SOCIALACCOUNT_PROVIDERS_GITLAB_SECRET
.. envvar:: RTD_SOCIALACCOUNT_PROVIDERS_BITBUCKET_OAUTH2_CLIENT_ID
.. envvar:: RTD_SOCIALACCOUNT_PROVIDERS_BITBUCKET_OAUTH2_SECRET
.. envvar:: RTD_SOCIALACCOUNT_PROVIDERS_GOOGLE_CLIENT_ID
.. envvar:: RTD_SOCIALACCOUNT_PROVIDERS_GOOGLE_SECRET

AWS configuration
~~~~~~~~~~~~~~~~~

The following variables can be used to use AWS in your local environment.
Useful for testing :doc:`temporary credentials </aws-temporary-credentials>`.

.. envvar:: RTD_S3_PROVIDER
.. envvar:: RTD_AWS_ACCESS_KEY_ID
.. envvar:: RTD_AWS_SECRET_ACCESS_KEY
.. envvar:: RTD_AWS_STS_ASSUME_ROLE_ARN
.. envvar:: RTD_S3_MEDIA_STORAGE_BUCKET
.. envvar:: RTD_S3_BUILD_COMMANDS_STORAGE_BUCKET
.. envvar:: RTD_S3_BUILD_TOOLS_STORAGE_BUCKET
.. envvar:: RTD_S3_STATIC_STORAGE_BUCKET
.. envvar:: RTD_AWS_S3_REGION_NAME

GitHub App
~~~~~~~~~~

You can use the following environment variables to set the settings used by the GitHub App:

.. envvar:: RTD_GITHUB_APP_ID
.. envvar:: RTD_GITHUB_APP_NAME
.. envvar:: RTD_GITHUB_APP_PRIVATE_KEY
.. envvar:: RTD_GITHUB_APP_WEBHOOK_SECRET

Ethical Ads variables
~~~~~~~~~~~~~~~~~~~~~

The following variables are required to use ``ethicalads`` in dev:

.. envvar:: RTD_USE_PROMOS
