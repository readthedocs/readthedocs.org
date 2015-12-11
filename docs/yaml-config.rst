Read the Docs YAML Config
=========================

Read the Docs now has support for configuring builds with a YAML file.
The file, 
`readthedocs.yml`,
must be in the root directory of your project.

.. note:: It isn't possible to configure all build settings with
	      this file currently.
	      We are working to add support for all configuration options soon.


Supported Settings
------------------

type
~~~~~~

Default: `sphinx`
Options: `[sphinx, mkdocs]`

The `type` block allows you to configure the build tool used for building your documentation.

.. code-block:: yaml

	type: sphinx

python
~~~~~~

The `python` block allows you to configure aspects of the Python executable used for building documentation.

* type

Default: `2`
Options: `[2, 3]`

.. code-block:: yaml

	python:
	   version: 3

conda
~~~~~

The `conda` block supports a `file` option::

* file

Default: `None`
Type: Path (specified from the root of the project)

The file option specified the Conda environment file to use.

.. code-block:: yaml

	conda:
	    file: environment.yml


Current Settings
----------------

* type
* python
* conda

Future Settings
---------------

* install_project
* requirements_file
* conf_file
* system_packages
