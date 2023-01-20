Feature Flags
=============

Read the Docs offers some additional flag settings
which are disabled by default for every project
and can only be enabled by `contacting us through our support form`_
or reaching out to the administrator of your service.

.. _contacting us through our support form: https://docs.readthedocs.io/en/stable/support.html

Available Flags
---------------

``CONDA_APPEND_CORE_REQUIREMENTS``: :featureflags:`CONDA_APPEND_CORE_REQUIREMENTS`

Makes Read the Docs to install all the requirements at once on ``conda create`` step.
This helps users to pin dependencies on conda and to improve build time.

``DONT_OVERWRITE_SPHINX_CONTEXT``: :featureflags:`DONT_OVERWRITE_SPHINX_CONTEXT`

``SKIP_SPHINX_HTML_THEME_PATH``: :featureflags:`SKIP_SPHINX_HTML_THEME_PATH`

When using sphinx-rtd-theme, ``html_theme_path`` is defined automatically in ``conf.py`` for older versions of Sphinx.
All projects created after January 2023 and projects using Sphinx 6+ skips the definition and do not need this feature flag.

If you need to explicitly block ``html_theme_path`` from being defined,
please state *why* you need this feature flag enabled,
as we will have to consider this a potential bug.

``DONT_CREATE_INDEX``: :featureflags:`DONT_CREATE_INDEX`

When Read the Docs detects that your project doesn't have an ``index.md`` or ``README.rst``,
it auto-generate one for you with instructions about how to proceed.

In case you are using a static HTML page as index or an generated index from code,
this behavior could be a problem. With this feature flag you can disable that.
