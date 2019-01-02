Feature Flags
=============

Read the Docs offers some additional flag settings which can be only be configured by the site admin.
These are optional settings and you might not need it for every project.
By default, these flags are disabled for every project.
A seperate request can be made by opening an issue on our `github`_ to enable
or disable one or more of these featured flags for a particular project.

.. _github: https://github.com/rtfd/readthedocs.org

Available Flags
---------------

USE_SPHINX_LATEST:
~~~~~~~~~~~~~~~~~~

Use latest version of Sphinx in building the project.

USE_SETUPTOOLS_LATEST:
~~~~~~~~~~~~~~~~~~~~~~

Use latest version of setuptools in building the project.

ALLOW_DEPRECATED_WEBHOOKS:
~~~~~~~~~~~~~~~~~~~~~~~~~~

Allow deprecated webhook views.

PIP_ALWAYS_UPGRADE:
~~~~~~~~~~~~~~~~~~~

Always run:

.. code-block:: bash

    pip install --upgrade

before building the project.

SKIP_SUBMODULES:
~~~~~~~~~~~~~~~~

Skip git submodule checkout.

DONT_OVERWRITE_SPHINX_CONTEXT:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Do not overwrite context vars in conf.py with Read the Docs context.

ALLOW_V2_CONFIG_FILE:
~~~~~~~~~~~~~~~~~~~~~

Allow to use the v2 of the configuration file.

MKDOCS_THEME_RTD:
~~~~~~~~~~~~~~~~~

Use Read the Docs theme for MkDocs as default theme.
