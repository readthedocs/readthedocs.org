Specifying your dependencies with Poetry
========================================

Declaring your project metadata
-------------------------------

Poetry is a :pep:`517`-compliant build backend, which means that
`it generates your project
metadata <https://python-poetry.org/docs/pyproject/#poetry-and-pep-517>`_
using a standardized interface that can be consumed directly by pip.
Therefore, by making sure that
the ``build-system`` section of your ``pyproject.toml``
declares the build backend as follows:

.. code-block:: toml
   :caption: pyproject.toml

   [build-system]
   requires = ["poetry_core>=1.0.0"]
   build-backend = "poetry.core.masonry.api"

You will be able to install it on Read the Docs just using pip,
using a configuration like this:

.. code-block:: yaml
   :caption: .readthedocs.yaml
   :emphasize-lines: 8-11

   version: 2

   build:
     os: ubuntu-20.04
     tools:
       python: "3.9"

   python:
     install:
       - method: pip
         path: .

For example, the `rich <https://rich.readthedocs.io/>`_ Python library
`uses Poetry <https://github.com/willmcgugan/rich/blob/ba5d0c2c/pyproject.toml#L49-L51>`_
to declare its library dependencies
and installs itself on Read the Docs
`with pip <https://github.com/willmcgugan/rich/blob/ba5d0c2c/.readthedocs.yml#L18-L19>`_.
