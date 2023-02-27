Feature flags
=============

.. **Please don't add more stuff here**. We want to move user-facing options to the config file.

Read the Docs offers a few additional settings that are otherwise disabled by default.
These specific settings are called *feature flags* and can only be enabled by `contacting us through our support form`_
or reaching out to the administrator of your service.

.. _contacting us through our support form: https://docs.readthedocs.io/en/stable/support.html

Available flags
---------------

``CONDA_APPEND_CORE_REQUIREMENTS``: Append Read the Docs core requirements to environment.yml file.

Makes Read the Docs to install all the requirements at once on ``conda create`` step.
This helps users to pin dependencies on conda and to improve build time.

``DONT_OVERWRITE_SPHINX_CONTEXT``: Do not overwrite context vars in conf.py with Read the Docs context.

``DONT_CREATE_INDEX``: Do not create index.md or README.rst if the project does not have one.

When Read the Docs detects that your project doesn't have an ``index.md`` or ``README.rst``,
it auto-generate one for you with instructions about how to proceed.

In case you are using a static HTML page as index or an generated index from code,
this behavior could be a problem. With this feature flag you can disable that.
