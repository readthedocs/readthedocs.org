Feature Flags
=============

Read the Docs offers some additional flag settings which can be only be configured by the site admin.
These are optional settings and you might not need it for every project.
By default, these flags are disabled for every project.
A separate request can be made by `contacting us via email`_ to enable
or disable one or more of these featured flags for a particular project.

.. _contacting us via email: mailto:support@readthedocs.org

Available Flags
---------------

``PIP_ALWAYS_UPGRADE``: :featureflags:`PIP_ALWAYS_UPGRADE`

``DONT_INSTALL_DOCUTILS``: :featureflags:`DONT_INSTALL_DOCUTILS`

``UPDATE_CONDA_STARTUP``: :featureflags:`UPDATE_CONDA_STARTUP`

The version of ``conda`` used in the build process could not be the latest one.
This is because we use Miniconda, which its release process is a little more slow than ``conda`` itself.
In case you prefer to use the latest ``conda`` version available, this is the flag you need.

``CONDA_APPEND_CORE_REQUIREMENTS``: :featureflags:`CONDA_APPEND_CORE_REQUIREMENTS`

Makes Read the Docs to install all the requirements at once on ``conda create`` step.
This helps users to pin dependencies on conda and to improve build time.

``CONDA_USES_MAMBA``: :featureflags:`CONDA_USES_MAMBA`

``conda`` solver consumes 1Gb minimum when installing any package using ``conda-forge`` channel.
This seems to be `a known issue`_ due conda forge has so many packages on it, among others.
Using this feature flag allows you to use mamba_ instead of ``conda`` to create the environment
and install the dependencies.
``mamba`` is a drop-in replacement for conda that it's much faster and also
reduces considerably the amount of memory required to solve the dependencies.

.. _mamba: https://quantstack.net/mamba.html
.. _a known issue: https://www.anaconda.com/understanding-and-improving-condas-performance/

``DONT_OVERWRITE_SPHINX_CONTEXT``: :featureflags:`DONT_OVERWRITE_SPHINX_CONTEXT`

``DONT_SHALLOW_CLONE``: :featureflags:`DONT_SHALLOW_CLONE`

The ``DONT_SHALLOW_CLONE`` flag is useful if your code accesses old commits during docs build,
e.g. python-reno release notes manager is known to do that
(error message line would probably include one of old Git commit id's).

``USE_TESTING_BUILD_IMAGE``: :featureflags:`USE_TESTING_BUILD_IMAGE`

``EXTERNAL_VERSION_BUILD``: :featureflags:`EXTERNAL_VERSION_BUILD`

``LIST_PACKAGES_INSTALLED_ENV``: :featureflags:`LIST_PACKAGES_INSTALLED_ENV`

``SHARE_SPHINX_DOCTREE``: :featureflags:`SHARE_SPHINX_DOCTREE`

By default, when Read the Docs runs Sphinx it passes a different output directory for the generated/parsed doctrees
(the argument ``-d _build/doctrees-{builder}`` is passed to ``sphinx-build``).
While this is a way to ensure that all the outputs are generated from scratch,
it may cause your builds to be slow if you have a big set of documentation and builds multiple formats.
In that case, enabling ``SHARE_SPHINX_DOCTREE`` could help to speed up your builds by sharing the doctree among all the formats.

``DONT_CREATE_INDEX``: :featureflags:`DONT_CREATE_INDEX`

When Read the Docs detects that your project doesn't have an ``index.md`` or ``README.rst``,
it auto-generate one for you with instructions about how to proceed.

In case you are using a static HTML page as index or an generated index from code,
this behavior could be a problem. With this feature flag you can disable that.
