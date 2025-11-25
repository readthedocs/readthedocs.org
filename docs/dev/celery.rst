Celery Tasks
============

Read the Docs uses `Celery <https://docs.celeryproject.org/>`_ for asynchronous task processing.
Tasks are distributed across different queues and handle various operations from building documentation
to sending notifications.

Task Queues
-----------

Tasks are organized into several queues:

* ``web`` - General web-related tasks (webhooks, notifications, search indexing)
* ``build:default`` - Standard documentation builds
* ``build:large`` - Builds for projects using conda or requiring more resources
* ``autoscaling`` - Metrics collection tasks (in readthedocs-ext)

Task Organization
-----------------

Tasks are organized by functional area:

**Build Tasks** (``readthedocs/builds/tasks.py``)
    Core build management tasks including archiving, version sync, and notifications.

**Project Build Tasks** (``readthedocs/projects/tasks/builds.py``)
    Main documentation building tasks:

    * ``sync_repository_task`` - Syncs repository branches/tags
    * ``update_docs_task`` - Builds documentation (main entry point)

**OAuth Tasks** (``readthedocs/oauth/tasks.py``)
    VCS integration tasks for syncing repositories and handling webhooks.

**Search Tasks** (``readthedocs/search/tasks.py``)
    Elasticsearch indexing and search query analytics.

**Analytics Tasks** (``readthedocs/analytics/tasks.py``)
    Page view analytics and data retention.

**Core Tasks** (``readthedocs/core/tasks.py``)
    Email sending, Redis cleanup, and object deletion.

Key Tasks
---------

update_docs_task
~~~~~~~~~~~~~~~~

The main entry point for building documentation. This task:

* Clones the repository
* Sets up the build environment (Docker or local)
* Installs dependencies
* Builds documentation in multiple formats
* Uploads artifacts to storage
* Handles failures and retries

It uses the ``UpdateDocsTask`` base class which provides:

* Automatic retries for ``BuildMaxConcurrencyError``
* Comprehensive error handling
* Build state tracking
* Notification sending

sync_versions_task
~~~~~~~~~~~~~~~~~~

Syncs version data from the VCS repository to the database:

* Creates new ``Version`` objects for tags/branches
* Deletes versions that no longer exist in the repository
* Runs automation rules
* Updates stable/latest version pointers
* Triggers builds for new stable versions

send_build_status
~~~~~~~~~~~~~~~~~

Sends build status to GitHub/GitLab for pull requests and commits.
Integrates with OAuth services to post commit statuses.

Custom Task Base Classes
-------------------------

PublicTask
~~~~~~~~~~

Located in ``readthedocs/core/utils/tasks/public.py``.

Base class for tasks with publicly viewable status. Features:

* Permission checking via ``check_permission`` decorator
* Public data exposure for UI consumption
* Graceful exception handling
* Task state updates

Example usage:

.. code-block:: python

   @PublicTask.permission_check(user_id_matches_or_superuser)
   @app.task(queue="web", base=PublicTask)
   def sync_remote_repositories(user_id):
       # Task implementation
       pass

SyncRepositoryMixin
~~~~~~~~~~~~~~~~~~~

Provides common functionality for repository synchronization tasks,
including VCS operations and version syncing logic.

Task Routing
------------

The ``TaskRouter`` class (``readthedocs/builds/tasks.py``) dynamically routes
build tasks to appropriate queues based on:

* Project configuration (``build_queue`` setting)
* Conda usage (routes to ``build:large``)
* Project maturity (new projects get ``build:large``)
* External version builds (use same queue as default version)

Best Practices
--------------

When creating new tasks:

1. **Choose the right queue**: Use ``web`` for most tasks, ``build:*`` only for builds
2. **Set appropriate timeouts**: Use ``time_limit`` and ``soft_time_limit``
3. **Handle exceptions**: Use ``throws`` tuple for expected exceptions
4. **Log context**: Use ``structlog.contextvars.bind_contextvars`` for structured logging
5. **Use locks for uniqueness**: Use ``memcache_lock`` for tasks that shouldn't run concurrently
6. **Bind tasks when needed**: Use ``bind=True`` to access ``self`` in the task

Example task definition:

.. code-block:: python

   @app.task(
       queue="web",
       bind=True,
       max_retries=3,
       default_retry_delay=60,
       time_limit=300,
   )
   def my_task(self, project_pk):
       structlog.contextvars.bind_contextvars(
           project_pk=project_pk,
       )
       log.info("Starting task")
       # Task implementation
       pass

Monitoring
----------

* Task execution is logged with structured logging (structlog)
* Build tasks report progress through state updates
* Metrics are collected via periodic tasks (readthedocs-ext)
* Failed tasks are tracked in Sentry

See Also
--------

* `Celery Documentation <https://docs.celeryproject.org/>`_
* :doc:`install` - Setting up development environment
* :doc:`tests` - Testing Celery tasks
