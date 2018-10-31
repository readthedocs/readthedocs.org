Specifying Dependencies
=======================

Any dependencies required for building a documentation project can be specified using a pip requirements file or a conda environment file.

.. note:: For the purpose of building your documentation with RTD, *project* is the documentation project, and *project root* is the directory where all the documentation is stored, often named ``docs``. 

Specifying a requirements file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The requirements file option is useful for specifying dependencies required for building the documentation. Additional uses specific to Read the Docs are mentioned at the end of this guide.

For details about the purpose of pip requirements file and how to create one, check out `pip user guide`_.

To use the requirements file, create and place the requirements file in the root directory of your documentation directory. For example::

    docs/requirements.txt

Using the YAML configuration file
---------------------------------

The recommended approach for specifying a pip requirements file is to use a ``readthedocs.yml`` file. 

The file's path should be relative to documentation root.

.. code-block:: yaml

    requirements_file: requirements.txt

See :doc:`/yaml-config` for setting up the .yml file

Using the project admin dashboard
---------------------------------

Once the requirements file has been created;

- Login to Read the Docs and go to the project admin dashboard.
- Go to ``Admin > Advanced Settings > Requirements file``.
- Specify the path of the requirements file you just created. The path should be relative to the root directory of the documentation project.

Using a conda environment file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If using conda, the dependencies can be specified in the conda environment file, ``environment.yml`` .

More on Read the Doc's conda support: :doc:`/conda`

Working with `conda and environment.yml`_

.. note:: Conda is only supported via the YAML file.

This conda environment file can be specified in ``readthedocs.yml`` in the ``conda`` block. 

.. code-block:: yaml

    conda:
        file: environment.yml

As before, the path should be relative to the documentation repository root.

.. _`pip user guide`: https://pip.pypa.io/en/stable/user_guide/#requirements-files
.. _`conda and environment.yml`: https://conda.io/docs/user-guide/tasks/manage-environments.html
