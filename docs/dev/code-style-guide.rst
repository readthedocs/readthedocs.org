Code architecture and style guide
=================================

This is the canonical reference for code-level conventions in
``readthedocs/readthedocs.org``. It complements :doc:`/style-guide` (which
covers documentation prose) and the repo-level ``AGENTS.md`` (tooling and
workflow).

Agents and contributors should skim this before opening a PR. Keep it short —
if a rule can be enforced by a linter or by reading the neighbouring file,
prefer that over adding prose here.

See also:

- ``AGENTS.md`` — commits, tests, tox, package management (``uv``).
- ``.ruff.toml`` — linter config is the source of truth for formatting.
- :doc:`/style-guide` — prose and RST conventions for docs.


Repository layout
-----------------

Django project apps live under ``readthedocs/``. A typical app follows:

.. code-block:: text

   readthedocs/<app>/
       models.py          # Django models; thin, delegate to querysets/managers
       querysets.py       # Custom QuerySet classes (one per model file)
       managers.py        # Custom Manager classes when needed
       views/             # Package preferred over single views.py for larger apps
       forms.py
       tasks/             # Celery tasks, split by concern (builds.py, search.py)
       migrations/        # Use ``tox -e migrations`` after any change
       signals.py
       tests/             # Test files named ``test_<area>.py``
       constants.py       # Module-level constants, UPPER_SNAKE_CASE
       exceptions.py      # App-specific exceptions

API code is split by version: ``readthedocs/api/v2/`` (internal, used by
builders) and ``readthedocs/api/v3/`` (public, DRF ViewSets). Do not add new
endpoints to v2 unless the builder needs them.

Proxito (``readthedocs/proxito/``) serves built documentation and has its own
settings module (``readthedocs.settings.proxito.*``). It must not import from
the dashboard views.


Python style
------------

Formatting and imports are enforced by Ruff (``tox -e pre-commit``). The
non-obvious conventions reviewers call out:

- **One import per line.** ``from x import A`` then ``from x import B`` on the
  next line — never ``from x import A, B``. Ruff's ``force-single-line`` is on.
- **Absolute imports** from ``readthedocs.<app>`` across apps. Relative
  (``from .constants import ...``) is fine inside the same app.
- **Type hints** on new function signatures. Don't retrofit the whole file;
  add them to what you touch.
- **Docstrings** on public classes and non-trivial functions. One-line summary
  in the imperative mood; expand below only if the "why" is non-obvious.
- Module-level ``"""Short module docstring."""`` at the top of new files.
- No comments that restate the code. Only write a comment when the *reason* is
  non-obvious (workaround, invariant, hidden constraint).


Logging
-------

Use ``structlog`` with keyword arguments — never f-strings or ``%`` formatting
in log calls. The log message stays a constant, context goes in kwargs:

.. code-block:: python

   import structlog
   log = structlog.get_logger(__name__)

   log.info(
       "Stable version updated.",
       project_slug=project.slug,
       version_identifier=version.identifier,
   )

Use ``log.exception(...)`` inside ``except`` blocks. Reserve ``log.error`` for
cases without a live traceback.


Django and DRF patterns
-----------------------

**Models.** Keep ``models.py`` focused on fields, validation, and short
methods. Push query logic into ``querysets.py``. Sensitive/extensible logic
that differs between .org and .com should use ``SettingsOverrideObject`` (see
``readthedocs/core/utils/extend.py``) instead of ``if settings.RTD_...``.

**QuerySets.** Name classes ``<Model>QuerySet`` (or ``<Model>QuerySetBase``
when the class is wrapped by ``SettingsOverrideObject``). Expose them on the
model via ``objects = <Model>QuerySet.as_manager()``.

**Views.** Class-based views for dashboard pages; DRF ViewSets for API v3.
New v3 ViewSets inherit from ``APIv3Settings`` in
``readthedocs/api/v3/views.py`` so throttling/auth/pagination stay consistent.

**Serializers.** v3 uses ``rest_flex_fields``. Split serializers by action
(``ProjectCreateSerializer``, ``ProjectUpdateSerializer``,
``ProjectSerializer`` for read) rather than overriding fields per-verb.

**Permissions.** Use the existing permission classes in
``readthedocs/api/v3/permissions.py`` and ``readthedocs/core/permissions.py``
(``AdminPermission``). Do not re-implement admin/member checks inline.

**Celery tasks.** Live in ``<app>/tasks.py`` or ``<app>/tasks/<area>.py``.
Task functions take only JSON-serializable arguments (pass ``project.pk``,
not ``project``). Tasks that affect builds should use ``memcache_lock`` to
prevent duplicate runs (see ``readthedocs/builds/utils.py``).

**Signals.** Put receivers in ``signals.py`` or ``signals_receivers.py`` and
connect them in ``apps.py``. Avoid business logic in ``post_save`` — prefer
explicit calls from the code path that caused the change.


Migrations
----------

- Always run ``tox -e migrations`` after touching a model or adding a
  migration. CI will fail otherwise.
- Name files descriptively:
  ``NNNN_<what_changed_in_snake_case>.py`` (e.g. ``0161_addons_notifications_show_on_external_default_false.py``).
- Set ``safe = Safe.before_deploy()`` / ``.after_deploy()`` on every new
  migration (``django_safemigrate``). Choose based on whether the running app
  can tolerate the old or new schema.
- Data migrations go in their own file, separate from schema changes, with
  both ``forwards`` and ``backwards`` (or ``migrations.RunPython.noop``).


Notifications and errors
------------------------

User-visible errors go through the notifications system, not ad-hoc strings:

- Add a ``Message`` to ``readthedocs/notifications/messages.py`` with a stable
  ``id`` (``generic-with-settings-link``, ``project:invalid:name``, etc.).
- Raise typed exceptions from ``<app>/exceptions.py`` (e.g. ``BuildUserError``,
  ``ProjectConfigurationError``) with the message ``id``. Don't raise bare
  ``Exception`` or return HTTP 500 for user-caused problems.
- Internal errors may use ``structlog`` only; don't expose tracebacks to users.


Testing
-------

See ``AGENTS.md`` for tox commands. Conventions:

- Use ``pytest`` style assertions (``assert foo == bar``). Legacy files use
  ``self.assertEqual`` — match the surrounding file, don't mix in one class.
- ``from django_dynamic_fixture import get`` to build model instances. Prefer
  it over hand-building fixtures.
- One behaviour per test. Name tests after what they assert:
  ``test_repository_full_name_with_ssh_url``.
- Put tests under ``<app>/tests/test_<area>.py``. Integration-style tests
  that span apps go in ``readthedocs/rtd_tests/``.
- Pytest marks (``search``, ``proxito``, ``embed_api``) are declared in
  ``pytest.ini`` and excluded from the default ``py312`` env. Mark new
  tests that need Elasticsearch or proxito settings accordingly.


Security
--------

- Never trust data from ``.readthedocs.yaml``, webhook payloads, or
  user-supplied URLs. Use the validators in ``<app>/validators.py``.
- Filesystem paths derived from user input must go through
  ``readthedocs.core.utils.filesystem.assert_path_is_inside_docroot``.
- External HTTP calls use ``readthedocs.core.utils.requests`` (timeouts,
  allowed-host checks) rather than ``requests`` directly.
- Shell interpolation: use ``shlex.quote`` or pass args as a list; never
  ``f"... {user_value}"`` into ``subprocess`` with ``shell=True``.


Front-end
---------

Templates, CSS, and JS live in the separate ``readthedocs/ext-theme``
repository. Changes in this repo are limited to template overrides in
``readthedocs/templates/`` and server-rendered context. If a change requires
new CSS/JS, open a companion PR in ``ext-theme``.
