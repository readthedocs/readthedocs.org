Feature Flags
=============

Read the Docs offers some additional flag settings
which are disabled by default for every project
and can only be enabled by `contacting us through our support form`_
or reaching out to the administrator of your service.

.. _contacting us through our support form: https://docs.readthedocs.io/en/stable/support.html

Available Flags
---------------

``PIP_ALWAYS_UPGRADE``: :featureflags:`PIP_ALWAYS_UPGRADE`

``UPDATE_CONDA_STARTUP``: :featureflags:`UPDATE_CONDA_STARTUP`

The version of ``conda`` used in the build process could not be the latest one.
This is because we use Miniconda, which its release process is a little more slow than ``conda`` itself.
In case you prefer to use the latest ``conda`` version available, this is the flag you need.

``CONDA_APPEND_CORE_REQUIREMENTS``: :featureflags:`CONDA_APPEND_CORE_REQUIREMENTS`

Makes Read the Docs to install all the requirements at once on ``conda create`` step.
This helps users to pin dependencies on conda and to improve build time.

``DONT_OVERWRITE_SPHINX_CONTEXT``: :featureflags:`DONT_OVERWRITE_SPHINX_CONTEXT`

``DONT_SHALLOW_CLONE``: :featureflags:`DONT_SHALLOW_CLONE`

The ``DONT_SHALLOW_CLONE`` flag is useful if your code accesses old commits during docs build,
e.g. python-reno release notes manager is known to do that
(error message line would probably include one of old Git commit id's).

``LIST_PACKAGES_INSTALLED_ENV``: :featureflags:`LIST_PACKAGES_INSTALLED_ENV`

``DONT_CREATE_INDEX``: :featureflags:`DONT_CREATE_INDEX`

When Read the Docs detects that your project doesn't have an ``index.md`` or ``README.rst``,
it auto-generate one for you with instructions about how to proceed.

In case you are using a static HTML page as index or an generated index from code,
this behavior could be a problem. With this feature flag you can disable that.
