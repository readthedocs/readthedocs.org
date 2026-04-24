Code architecture and style guide
=================================

Project-specific patterns for ``readthedocs/readthedocs.org``. Complements
``AGENTS.md`` (tooling, workflow, PEP 8 basics) and :doc:`/style-guide` (prose).
Only rules that reviewers repeat or that a linter can't enforce live here.


Repository layout
-----------------

Django apps live under ``readthedocs/<app>/``. Non-obvious conventions:

- Query logic goes in ``querysets.py`` / ``managers.py``, not ``models.py``.
- ``tasks/`` as a package (split by concern: ``builds.py``, ``search.py``) is
  preferred over a single ``tasks.py`` once an app grows past a few tasks.
- ``views/`` as a package once an app has more than one view module.
- API is split by version: v2 (``readthedocs/api/v2/``) is internal to the
  builder; v3 (``readthedocs/api/v3/``) is public. Add new endpoints to v3.
- Proxito (``readthedocs/proxito/``) serves built docs, uses its own settings
  module, and must not import from dashboard views.


Imports and logging
-------------------

- **One import per line**, enforced by Ruff's ``force-single-line``. Never
  ``from x import A, B``.
- Absolute imports (``from readthedocs.<app> import ...``) across apps;
  relative imports only within the same app.
- Logging uses ``structlog`` with keyword arguments — the message is a
  constant, context goes in kwargs. No f-strings or ``%`` formatting in logs:

  .. code-block:: python

     log = structlog.get_logger(__name__)
     log.info("Stable version updated.", project_slug=project.slug)

- ``log.exception(...)`` inside ``except`` blocks; ``log.error`` only when
  there is no live exception context.


Django and DRF
--------------

- **QuerySets.** Named ``<Model>QuerySet``; exposed via
  ``objects = <Model>QuerySet.as_manager()``. Use ``<Model>QuerySetBase`` when
  the class is wrapped by ``SettingsOverrideObject``.
- **.org vs .com branching.** Use ``SettingsOverrideObject`` (see
  ``readthedocs/core/utils/extend.py``), not ``if settings.RTD_...``.
- **Permissions.** Reuse ``AdminPermission`` and the classes in
  ``readthedocs/api/v3/permissions.py``. Don't re-implement membership checks.
- **API v3 ViewSets** inherit from ``APIv3Settings``
  (``readthedocs/api/v3/views.py``) for consistent throttling/auth/pagination.
  Split serializers by action (``ProjectCreateSerializer``,
  ``ProjectUpdateSerializer``, ``ProjectSerializer``) rather than switching
  fields per verb.
- **Celery tasks** take only JSON-serializable arguments (pass ``project.pk``,
  not ``project``). Build-affecting tasks use ``memcache_lock``
  (``readthedocs/builds/utils.py``) to prevent duplicate runs.
- **Signals.** Keep receivers thin; prefer explicit calls from the code path
  that caused the change over business logic in ``post_save``.


Migrations
----------

- Set ``safe = Safe.before_deploy()`` / ``.after_deploy()`` on every new
  migration (``django_safemigrate``).
- Put data migrations in their own file, separate from schema changes, and
  provide a reverse (or ``migrations.RunPython.noop``).


Errors and notifications
------------------------

- User-visible errors: add a ``Message`` to
  ``readthedocs/notifications/messages.py`` with a stable ``id`` and raise a
  typed exception from ``<app>/exceptions.py`` (``BuildUserError``,
  ``ProjectConfigurationError``, …) — don't raise bare ``Exception`` or
  surface stack traces.


Testing
-------

- Build fixtures with ``django_dynamic_fixture.get``.
- Match the surrounding file's assertion style (``assert ==`` vs
  ``self.assertEqual``); don't mix within a class.
- Mark tests that need Elasticsearch / proxito settings with the ``search``,
  ``proxito``, or ``embed_api`` pytest marks — the default ``py312`` env
  excludes them.


Security
--------

- Validate user input via ``<app>/validators.py``.
- Filesystem paths from user input go through
  ``readthedocs.core.utils.filesystem.assert_path_is_inside_docroot``.
- External HTTP uses ``readthedocs.core.utils.requests`` (timeouts,
  allowed-host checks), not ``requests`` directly.
- Never interpolate user values into ``subprocess`` with ``shell=True``; pass
  arguments as a list or use ``shlex.quote``.
