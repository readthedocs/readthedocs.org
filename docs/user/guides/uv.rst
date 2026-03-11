Using ``uv`` on Read the Docs
=============================

`uv <https://github.com/astral-sh/uv/>`__ can be used on Read the Docs to install documentation dependencies quickly.
You can use it as a full project manager with ``uv.lock``,
or as a faster installer for existing ``requirements.txt`` files.

This guide shows recommended patterns for both Sphinx and MkDocs projects.

.. contents:: Contents
   :local:
   :depth: 2

Recommended approach: ``uv`` project with ``uv.lock``
------------------------------------------------------

For most projects, we recommend:

* Defining docs dependencies in a ``docs`` dependency group in ``pyproject.toml``.
* Committing ``uv.lock`` to your repository.
* Using ``uv sync --frozen`` in Read the Docs builds.
* Pinning your ``uv`` version instead of using ``latest``.

This gives you the most :term:`reproducible` setup and keeps local and hosted builds aligned.

.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2

   sphinx:
     configuration: docs/conf.py

   build:
     os: "ubuntu-24.04"
     tools:
       python: "3.13"
     jobs:
       pre_create_environment:
         - asdf plugin add uv
         - asdf install uv 0.10.6
         - asdf global uv 0.10.6
       create_environment:
         - uv venv "$READTHEDOCS_VIRTUALENV_PATH"
       install:
         - UV_PROJECT_ENVIRONMENT="$READTHEDOCS_VIRTUALENV_PATH" uv sync --frozen --group docs

.. note::

   If your docs require optional dependencies,
   add them with ``--extra <name>`` or ``--all-extras`` in the ``uv sync`` command.

Alternative: ``uv`` project without lock file enforcement
---------------------------------------------------------

If you do not commit ``uv.lock`` yet,
or if you intentionally want dependency updates during builds,
you can drop ``--frozen``:

.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2

   sphinx:
     configuration: docs/conf.py

   build:
     os: "ubuntu-24.04"
     tools:
       python: "3.13"
     jobs:
       pre_create_environment:
         - asdf plugin add uv
         - asdf install uv 0.10.6
         - asdf global uv 0.10.6
       create_environment:
         - uv venv "$READTHEDOCS_VIRTUALENV_PATH"
       install:
         - UV_PROJECT_ENVIRONMENT="$READTHEDOCS_VIRTUALENV_PATH" uv sync --group docs

This is easier to adopt quickly,
but it is less reproducible than using ``uv.lock`` with ``--frozen``.

Alternative: use ``uv`` with ``requirements.txt``
-------------------------------------------------

If your project is not managed as a ``uv`` project,
you can still use ``uv`` as an installer for existing requirements files:

.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2

   sphinx:
     configuration: docs/conf.py

   build:
     os: "ubuntu-24.04"
     tools:
       python: "3.13"
     jobs:
       pre_create_environment:
         - asdf plugin add uv
         - asdf install uv 0.10.6
         - asdf global uv 0.10.6
       create_environment:
         - uv venv "$READTHEDOCS_VIRTUALENV_PATH"
       install:
         - uv pip install --python "$READTHEDOCS_VIRTUALENV_PATH/bin/python" -r docs/requirements.txt

.. tip::

    If your build imports your package itself,
    install it in the same step with ``uv pip install --python "$READTHEDOCS_VIRTUALENV_PATH/bin/python" .``.

Using ``uv`` with MkDocs
------------------------

The same ``uv`` installation patterns work with MkDocs.
Only the tool-specific configuration changes:

.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2

   mkdocs:
     configuration: mkdocs.yml

   build:
     os: "ubuntu-24.04"
     tools:
       python: "3.13"
     jobs:
       pre_create_environment:
         - asdf plugin add uv
         - asdf install uv 0.10.6
         - asdf global uv 0.10.6
       create_environment:
         - uv venv "$READTHEDOCS_VIRTUALENV_PATH"
       install:
         - UV_PROJECT_ENVIRONMENT="$READTHEDOCS_VIRTUALENV_PATH" uv sync --frozen --group docs

Recommendations
---------------

* Pin ``build.os`` and ``build.tools.python`` in ``.readthedocs.yaml``.
* Pin your ``uv`` version in ``asdf install uv 0.10.6``.
* Prefer ``uv.lock`` and ``uv sync --frozen`` for reproducible builds.
* Keep docs-only dependencies in a dedicated ``docs`` group.
* Set ``UV_PROJECT_ENVIRONMENT`` inline on the command using ``uv sync``.

.. seealso::

   :doc:`/guides/reproducible-builds`
      Recommendations for reproducible docs builds.
   :doc:`/build-customization`
      Learn more about the ``build.jobs`` customization model.
   :doc:`/reference/environment-variables`
      Reference for environment variables available in builds.
