Read the Docs YAML Config
=========================

Read the Docs now has support for configuring builds with a YAML file.
The file, ``readthedocs.yml`` (or ``.readthedocs.yml``), must be in the root directory of your project.

.. warning:: This feature is in a beta state.
             Please file an `issue`_ if you find anything wrong.

Supported Settings
------------------

formats
~~~~~~~

* Default: ``htmlzip``, ``pdf``, ``epub``
* Options: ``htmlzip``, ``pdf``, ``epub``, ``none``

The formats of your documentation you want to be built.
Choose ``none`` to build none of the formats.

.. note:: We will always build an HTML & JSON version of your documentation.
		  These are used for web serving & search indexing, respectively.

.. code-block:: yaml

    # Don't build any extra formats
    formats:
        - none

.. code-block:: yaml

    # Build PDF & ePub
    formats:
        - epub
        - pdf

requirements_file
~~~~~~~~~~~~~~~~~

* Default: `None`
* Type: Path (specified from the root of the project)

The path to your Pip requirements file.

.. code-block:: yaml

	requirements_file: requirements/docs.txt


conda
~~~~~

The ``conda`` block allows for configuring our support for Conda.

conda.file
``````````

* Default: `None`
* Type: Path (specified from the root of the project)

The file option specified the Conda `environment file`_ to use.


.. code-block:: yaml

	conda:
	    file: environment.yml

.. note:: Conda is only supported via the YAML file.

python
~~~~~~

The ``python`` block allows you to configure aspects of the Python executable
used for building documentation.

python.version
``````````````

* Default: ``2.7``
* Options: ``2.7``, ``2``, ``3.5``, ``3``

This is the version of Python to use when building your documentation. If you
specify only the major version of Python, the highest supported minor version
will be selected.

The supported Python versions depends on the version of the build image your
project is using. The default build image that is used to build documentation
contains support for Python ``2.7`` and ``3.5``.

There is also an image in testing that supports Python versions ``2.7``,
``3.3``, ``3.4``, ``3.5``, and ``3.6``. If you would like access to this build
image, you can sign up for beta access here:

https://goo.gl/forms/AKEoeWHixlzVfqKT2

.. code-block:: yaml

    python:
       version: 3.5

python.setup_py_install
```````````````````````

* Default: `False`
* Type: Boolean

When true, install your project into the Virtualenv with
``python setup.py install`` when building documentation.

.. code-block:: yaml

	python:
	   setup_py_install: true

python.pip_install
``````````````````

* Default: `False`
* Type: Boolean

When true, install your project into the Virtualenv with pip when building
documentation.

.. code-block:: yaml

    python:
       pip_install: true

.. To implement..

	type
	~~~~

    * Default: ``sphinx``
    * Options: ``sphinx``, ``mkdocs``

    The ``type`` block allows you to configure the build tool used for building
    your documentation.

	.. code-block:: yaml

		type: sphinx

	conf_file
	~~~~~~~~~

    * Default: `None`
    * Type: Path (specified from the root of the project)

    The path to a specific Sphinx ``conf.py`` file. If none is found, we will
    choose one.

	.. code-block:: yaml

		conf_file: project2/docs/conf.py

python.extra_requirements
`````````````````````````

* Default: ``[]``
* Type: List

List of `extra requirements`_ sections to install, additionally to the
`package default dependencies`_. Only works if ``python.pip_install`` option
above is set to ``True``.

Let's say your Python package has a ``setup.py`` which looks like this:

.. code-block:: python

    from setuptools import setup

    setup(
        name="my_package",
        # (...)
        install_requires=[
            'requests',
            'simplejson'],
        extras_require={
            'tests': [
                'nose',
                'pycodestyle >= 2.1.0'],
            'docs': [
                'sphinx >= 1.4',
                'sphinx_rtd_theme']}
    )

Then to have all dependencies from the ``tests`` and ``docs`` sections
installed in addition to the default ``requests`` and ``simplejson``, use the
``extra_requirements`` as such:

.. code-block:: yaml

    python:
        extra_requirements:
            - tests
            - docs

Behind the scene the following Pip command will be run:

.. code-block:: shell

    $ pip install -e .[tests,docs]


.. _issue: https://github.com/rtfd/readthedocs.org/issues
.. _environment file: http://conda.pydata.org/docs/using/envs.html#share-an-environment
.. _extra requirements: http://setuptools.readthedocs.io/en/latest/setuptools.html#declaring-extras-optional-features-with-their-own-dependencies
.. _package default dependencies: http://setuptools.readthedocs.io/en/latest/setuptools.html#declaring-dependencies
