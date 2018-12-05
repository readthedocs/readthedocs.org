Read the Docs YAML Config
=========================

Read the Docs now has support for configuring builds with a YAML file.
The file, ``readthedocs.yml``, must be in the root directory of your project.

.. warning:: This feature is in a beta state.
             Please file an `issue`_ if you find anything wrong.


Here is an example of what this file looks like:

.. code:: yaml

   # .readthedocs.yml

   build:
     image: latest
   
   python:
     version: 3.6
     setup_py_install: true


Supported settings
------------------

.. _yaml__formats:

formats
~~~~~~~

* Default: [``htmlzip``, ``pdf``, ``epub``]
* Options: ``htmlzip``, ``pdf``, ``epub``
* Type: List

The formats of your documentation you want to be built.
Set as an empty list ``[]`` to build none of the formats.

.. note:: We will always build an HTML & JSON version of your documentation.
		  These are used for web serving & search indexing, respectively.

.. code-block:: yaml

    # Don't build any extra formats
    formats: []

.. code-block:: yaml

    # Build PDF & ePub
    formats:
        - epub
        - pdf

.. _yaml__requirements_file:

requirements_file
~~~~~~~~~~~~~~~~~

* Default: ``null``
* Type: Path (specified from the root of the project)

The path to your pip requirements file.

.. code-block:: yaml

   requirements_file: requirements/docs.txt

.. _yaml__conda:

conda
~~~~~

The ``conda`` block allows for configuring our support for Conda.

conda.file
``````````

* Default: ``null``
* Type: Path (specified from the root of the project)

The file option specified the Conda `environment file`_ to use.

.. code-block:: yaml

   conda:
     file: environment.yml

.. note:: Conda is only supported via the YAML file.

.. _yaml__build:

build
~~~~~

The ``build`` block configures specific aspects of the documentation build.

.. _yaml__build__image:

build.image
```````````

* Default: :djangosetting:`DOCKER_IMAGE`
* Options: ``1.0``, ``2.0``, ``latest``

The build image to use for specific builds.
This lets users specify a more experimental build image,
if they want to be on the cutting edge.

Certain Python versions require a certain build image,
as defined here:

* ``1.0``: 2, 2.7, 3, 3.4
* ``2.0``: 2, 2.7, 3, 3.5
* ``latest``: 2, 2.7, 3, 3.3, 3.4, 3.5, 3.6

.. code-block:: yaml

    build:
        image: latest

    python:
        version: 3.6

.. _yaml__python:

python
~~~~~~

The ``python`` block allows you to configure aspects of the Python executable
used for building documentation.

.. _yaml__python__version:

python.version
``````````````

* Default: ``2.7``
* Options: ``2.7``, ``2``, ``3.5``, ``3``

This is the version of Python to use when building your documentation.
If you specify only the major version of Python,
the highest supported minor version will be selected.

.. warning:: 

    The supported Python versions depends on the version of the build image your
    project is using. The default build image that is used to build
    documentation contains support for Python ``2.7`` and ``3.5``.  See the
    :ref:`yaml__build__image` for more information on supported Python versions.

.. code-block:: yaml

    python:
       version: 3.5

python.use_system_site_packages
```````````````````````````````

* Default: ``false``
* Type: Boolean

When true, it gives the virtual environment access to the global site-packages directory.
Depending on the :ref:`yaml-config:build.image`,
Read the Docs includes some libraries like scipy, numpy, etc.
See :ref:`builds:The build environment` for more details.

.. code-block:: yaml

    python:
       use_system_site_packages: true

.. _yaml__python__setup_py_install:

python.setup_py_install
```````````````````````

* Default: ``false``
* Type: Boolean

When true, install your project into the Virtualenv with
``python setup.py install`` when building documentation.

.. code-block:: yaml

	python:
	   setup_py_install: true

.. _yaml__python__pip_install:

python.pip_install
``````````````````

* Default: ``false``
* Type: Boolean

When ``true``, install your project into the virtualenv with pip when building
documentation.

.. code-block:: yaml

    python:
       pip_install: true


.. TODO not yet implemented. We should move these to another doc.
.. ==============================================================
.. 
.. type
.. ~~~~
.. 
.. * Default: ``sphinx``
.. * Options: ``sphinx``, ``mkdocs``
.. 
.. The ``type`` block allows you to configure the build tool used for building
.. your documentation.
.. 
.. .. code-block:: yaml
.. 
..     type: sphinx
.. 
.. conf_file
.. ~~~~~~~~~
.. 
.. * Default: `None`
.. * Type: Path (specified from the root of the project)
.. 
.. The path to a specific Sphinx ``conf.py`` file. If none is found, we will
.. choose one.
.. 
.. .. code-block:: yaml
.. 
..     conf_file: project2/docs/conf.py

.. _yaml__python__extra_requirements:

python.extra_requirements
`````````````````````````

* Default: ``[]``
* Type: List

List of `extra requirements`_ sections to install, additionally to the
`package default dependencies`_. Only works if ``python.pip_install`` option
above is set to ``true``.

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
