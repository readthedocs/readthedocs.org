YAML Configuration File
=======================

Backgroud
---------

The current YAML configuration file is in beta state.
There are many options and features that it doesn't support yet.
This document will serve as a design document for discuss how to implement the missing features.

Scope
-----

- Finish the spec to include all the missing options
- Have consistency around the spec
- Proper documentation for the end user
- Allow to specify the spec's version used on the YAML file
- Show the YAML file on the build process
- Show/suggest a YAML file at the project creation if it hasn't one
- Have one source of truth for global configurations 

RTD settings
------------

No all the RTD settings are applicable to the YAML file,
others are applicable for each build (or version),
and others for the global project. 

Not applicable settings
~~~~~~~~~~~~~~~~~~~~~~~

Those settings can't be on the YAML file because:
may depend for the initial project setup,
are planned to be removed,
security and privacy reasons.

- Project Name
- Repo URL
- Repo type
- Privacy level (this feature is planned to be removed [#privacy-level]_)
- Project description (this feature is planned to be removed [#project-description]_)
- Single version (*)
- Default branch
- Default version (*)
- Domains (*)
- Active versions (*)
- Translations
- Subprojects
- Integrations
- Notifications

.. note::
   The items marked with ``(*)`` can be considered to be global settings.
   But aren't too relevant right now or aren't related to the builds.

Global settings
~~~~~~~~~~~~~~~

Those settings will be read from the YAML file on the ``default branch``.

- Language
- Programming Language
- Project homepage
- Tags
- Analytics code
- Redirects 

Local settings
~~~~~~~~~~~~~~

Those configurations will be read from the YAML file in the current version that is being built.

Several settings are already implemented and documented on
https://docs.readthedocs.io/en/latest/yaml-config.html.
So, they aren't covered with much detail here. 

- Documentation type
- Project installation (virtual env, requirements file, sphinx configuration file, etc)
- Additional builds (pdf, epub)
- Python interpreter

Configuration file
------------------

Format
~~~~~~

The file format is based on the YAML spec 1.2 [#yaml-spec]_
(latest version on the time of this writing).

The file must be on the root directory of the repository, and must be named as:

- ``.readthedocs.yml``
- ``readthedocs.yml``

Conventions
~~~~~~~~~~~

The spec of the configuration file must use this conventions.

- Use `[]` to indicate an empty list
- Use `null` to indicate a null value
- Use `all` (internal string keyword) to indicate that all options are included on a list with predetermined choices.
- Use `true`  and `false` as only options on boolean fields

Spec
~~~~

The current spec is documented on https://docs.readthedocs.io/en/latest/yaml-config.html
and https://github.com/rtfd/readthedocs-build/blob/master/docs/spec.rst

Versioning the spec
-------------------

TODO

Adoption of the configuration file
----------------------------------

When a user creates a new project or it's on the settings page,
we could suggest her/him an example of a functional configuration file with a minimal setup.

Main source for global configurations
-------------------------------------

There are some global settings that are needed for the build process (like language).
So it's needed to read this configurations from one source of truth before each build.
This source can be taken from the ``default branch`` setting.
RTD will checkout to this branch and read this configurations before the real build process starts.

That solves one problem, but RTD still need to know when to update the others global settings.
Would be a waste of resources to made a new build each time a global setting is updated for it to take effect.
Currently, RTD keeps a dedicated local repository for each version, which is updated before a build.
RTD could have a central repository for this operations [#one-checkout]_.

Configuration file and database options
---------------------------------------

To decouple the configuration file from the database and keep the compatibility with projects without one,
we need to generate a YAML file from the existing database options,
this will also help with the `Adoption of the configuration file`_.

The build process
-----------------

- The repository is updated
- Checkout to the default branch and read the global settings
- Checkout to the current version and read the local settings
- Before the build process the YAML file is shown (similar to ``cat config.py`` step).
- Try to parse the YAML file (the build fails if there is an error)
- The version is built according to the settings

Dependencies
------------

Current repository which contains the code related to the configuration file:
https://github.com/rtfd/readthedocs-build

Footnotes
---------

.. [#privacy-level] https://github.com/rtfd/readthedocs.org/issues/2663
.. [#project-description] https://github.com/rtfd/readthedocs.org/issues/3689
.. [#yaml-spec] http://yaml.org/spec/1.2/spec.html
.. [#one-checkout] https://github.com/rtfd/readthedocs.org/issues/1375
