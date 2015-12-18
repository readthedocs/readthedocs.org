Read the Docs YAML Config
=========================

Read the Docs now has support for configuring builds with a YAML file.
The file, 
`readthedocs.yml`,
must be in the root directory of your project.

.. warning:: This feature is in a beta state.
             Please file an Issue if you find anything wrong.

Supported Settings
------------------

conda
~~~~~

The `conda` block supports a `file` option:

* file

Default: `None`
Type: Path (specified from the root of the project)

The file option specified the Conda environment file to use.

.. code-block:: yaml

	conda:
	    file: environment.yml

.. note:: Conda is only supported via the YAML file.

python
~~~~~~

The `python` block allows you to configure aspects of the Python executable used for building documentation.

* version

Default: `2`
Options: `[2, 3]`

.. code-block:: yaml

	python:
	   version: 3

* setup_py_install

Default: `False`
Type: Boolean

.. code-block:: yaml

	python:
	   setup_py_install: true

requirements_file
~~~~~~~~~~~~~~~~~

Default: `None`
Type: Path (specified from the root of the project)

The path to your Pip requirements file.


.. code-block:: yaml

	requirements_file: requirements/docs.txt


.. To implement..

	type
	~~~~

	Default: `sphinx`
	Options: `[sphinx, mkdocs]`

	The `type` block allows you to configure the build tool used for building your documentation.

	.. code-block:: yaml

		type: sphinx
		
	conf_file
	~~~~~~~~~

	Default: `None`
	Type: Path (specified from the root of the project)

	The path to a specific Sphinx `conf.py` file. If none is found, we will choose one.

	.. code-block:: yaml

		conf_file: project2/docs/conf.py

