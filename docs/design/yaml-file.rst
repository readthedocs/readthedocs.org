YAML Configuration File
=======================

Background
----------

The current YAML configuration file is in beta state.
There are many options and features that it doesn't support yet.
This document will serve as a design document for discuss how to implement the missing features.

Scope
-----

- Finish the spec to include all the missing options
- Have consistency around the spec
- Proper documentation for the end user
- Allow to specify the spec's version used on the YAML file
- Collect/show metadata about the YAML file and build configuration
- Promote the adoption of the configuration file 

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
- Single version
- Default branch
- Default version
- Domains
- Active versions
- Translations
- Subprojects
- Integrations
- Notifications
- Language
- Programming Language
- Project homepage
- Tags
- Analytics code
- Global redirects

Global settings
~~~~~~~~~~~~~~~

To keep consistency with the per-version settings and avoid confusion,
this settings will not be stored in the YAML file and will be stored in the database only.

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
- Per-version redirects

Configuration file
------------------

Format
~~~~~~

The file format is based on the YAML spec 1.2 [#yaml-spec]_
(latest version on the time of this writing).

The file must be on the root directory of the repository, and must be named as:

- ``readthedocs.yml``
- ``readthedocs.yaml``
- ``.readthedocs.yml``
- ``.readthedocs.yaml``

Conventions
~~~~~~~~~~~

The spec of the configuration file must use this conventions.

- Use `[]` to indicate an empty list
- Use `null` to indicate a null value
- Use `all` (internal string keyword) to indicate that all options are included on a list with predetermined choices.
- Use `true`  and `false` as only options on boolean fields

Spec
~~~~

The current spec is documented on https://docs.readthedocs.io/en/latest/yaml-config.html.
It will be used as base for the future spec.
The spec will be written using a validation schema such as https://json-schema-everywhere.github.io/yaml.

Versioning the spec
-------------------

The version of the spec that the user wants to use will be specified on the YAML file.
The spec only will have mayor versions (1.0, not 1.2) [#specversioning]_.
For keeping compatibility with older projects using a configuration file without a version,
the latest compatible version will be used (1.0).

Adoption of the configuration file
----------------------------------

When a user creates a new project or it's on the settings page,
we could suggest her/him an example of a functional configuration file with a minimal setup.
And making clear where to put global configurations.

For users that already have a project,
we can suggest him/her a configuration file on each build based on the current settings.

Configuration file and database
-------------------------------

The settings used in the build from the configuration file
(and other metadata) needs to be stored in the database,
this is for later usage only, not to populate existing fields.

The build process
-----------------

- The repository is updated
- Checkout to the current version
- Retrieve the settings from the database
- Try to parse the YAML file (the build fails if there is an error)
- Merge the both settings (YAML file and database)
- The version is built according to the settings
- The settings used to build the documentation can be seen by the user

Dependencies
------------

Current repository which contains the code related to the configuration file:
https://github.com/rtfd/readthedocs-build

Footnotes
---------

.. [#privacy-level] https://github.com/rtfd/readthedocs.org/issues/2663
.. [#project-description] https://github.com/rtfd/readthedocs.org/issues/3689
.. [#yaml-spec] http://yaml.org/spec/1.2/spec.html
.. [#specversioning] https://github.com/rtfd/readthedocs.org/issues/3806
.. [#one-checkout] https://github.com/rtfd/readthedocs.org/issues/1375
