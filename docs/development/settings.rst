Interesting Settings
====================

DOCKER_LIMITS
-------------

Default: :djangosetting:`DOCKER_LIMITS`

A dictionary of limits to virtual machines. These limits include:

time
    An integer representing the total allowed time limit (in
    seconds) of build processes. This time limit affects the parent
    process to the virtual machine and will force a virtual machine
    to die if a build is still running after the allotted time
    expires.

memory
    The maximum memory allocated to the virtual machine. If this
    limit is hit, build processes will be automatically killed.
    Examples: '200m' for 200MB of total memory, or '2g' for 2GB of
    total memory.

SLUMBER_USERNAME
----------------

.. Don't set this automatically, lest we leak something. We are using the dev
   settings in the conf.py, but it's probably a good idea to be safe.

Default: ``test``

The username to use when connecting to the Read the Docs API. Used for hitting the API while building the docs.

SLUMBER_PASSWORD
----------------

.. Don't set this automatically, lest we leak something. We are using the dev
   settings in the conf.py, but it's probably a good idea to be safe.

Default: ``test``

The password to use when connecting to the Read the Docs API. Used for hitting the API while building the docs.

USE_SUBDOMAIN
---------------

Default: :djangosetting:`USE_SUBDOMAIN`

Whether to use subdomains in URLs on the site, or the Django-served content.
When used in production, this should be ``True``, as Nginx will serve this content.
During development and other possible deployments, this might be ``False``.

PRODUCTION_DOMAIN
------------------

Default: :djangosetting:`PRODUCTION_DOMAIN`

This is the domain that gets linked to throughout the site when used in production.
It depends on `USE_SUBDOMAIN`, otherwise it isn't used.

RTD_INTERSPHINX_URL
-------------------

Default: :djangosetting:`RTD_INTERSPHINX_URL`

This is the domain that is used to fetch the intersphinx inventory file.
If not set explicitly this is the ``PRODUCTION_DOMAIN``.

DEFAULT_PRIVACY_LEVEL
---------------------

Default: :djangosetting:`DEFAULT_PRIVACY_LEVEL`

What privacy projects default to having. Generally set to `public`. Also acts as a proxy setting for blocking certain historically insecure options, like serving generated artifacts directly from the media server.

INDEX_ONLY_LATEST
-----------------

Default: :djangosetting:`INDEX_ONLY_LATEST`

In search, only index the `latest` version of a Project.

PUBLIC_DOMAIN
-------------

Default: :djangosetting:`PUBLIC_DOMAIN`

A special domain for serving public documentation.
If set, public docs will be linked here instead of the `PRODUCTION_DOMAIN`.


PUBLIC_DOMAIN_USES_HTTPS
------------------------

Default: ``False``

If ``True`` and ``PUBLIC_DOMAIN`` is set, that domain will default to
serving public documentation over HTTPS. By default, documentation is
served over HTTP.


ALLOW_ADMIN
-----------

Default: :djangosetting:`ALLOW_ADMIN`

Whether to include `django.contrib.admin` in the URL's.


RTD_BUILD_MEDIA_STORAGE
-----------------------

Default: ``readthedocs.builds.storage.BuildMediaFileSystemStorage``

Use this storage class to upload build artifacts to cloud storage (S3, Azure storage).
This should be a dotted path to the relevant class (eg. ``'path.to.MyBuildMediaStorage'``).
Your class should mixin :class:`readthedocs.builds.storage.BuildMediaStorageMixin`.


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

Default: :djangosetting:`ES_TASK_CHUNK_SIZE`

The maximum number of data send to each elasticsearch indexing celery task.
This has been used while running ``elasticsearch_reindex`` management command.


ES_PAGE_IGNORE_SIGNALS
----------------------

Default: ``False``

This settings is used to determine whether to index each page separately into elasticsearch.
If the setting is ``True``, each ``HTML`` page will not be indexed separately but will be
indexed by bulk indexing.


ELASTICSEARCH_DSL_AUTOSYNC
--------------------------

Default: ``True``

This setting is used for automatically indexing objects to elasticsearch.
``False`` by default in development so it is possible to create
project and build documentations without having elasticsearch.


.. _elasticsearch-dsl-py.connections.configure: https://elasticsearch-dsl.readthedocs.io/en/stable/configuration.html#multiple-clusters
