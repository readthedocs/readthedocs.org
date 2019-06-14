Feature Flags
=============

Read the Docs offers some additional flag settings which can be only be configured by the site admin.
These are optional settings and you might not need it for every project.
By default, these flags are disabled for every project.
A separate request can be made by opening an issue on our `github`_ to enable
or disable one or more of these featured flags for a particular project.

.. _github: https://github.com/rtfd/readthedocs.org

Available Flags
---------------

``PIP_ALWAYS_UPGRADE``: :featureflags:`PIP_ALWAYS_UPGRADE`

``DONT_OVERWRITE_SPHINX_CONTEXT``: :featureflags:`DONT_OVERWRITE_SPHINX_CONTEXT`

``DONT_SHALLOW_CLONE``: :featureflags:`DONT_SHALLOW_CLONE`

The ``DONT_SHALLOW_CLONE`` flag is useful if your code accesses old commits during docs build,
e.g. python-reno release notes manager is known to do that
(error message line would probably include one of old Git commit id's).

``USE_TESTING_BUILD_IMAGE``: :featureflags:`USE_TESTING_BUILD_IMAGE`