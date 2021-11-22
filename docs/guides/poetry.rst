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

Locking your dependencies
-------------------------

With you ``pyproject.toml`` file you are free to `specify the dependency
versions <https://python-poetry.org/docs/dependency-specification/>`_
that are more appropriate for your project,
either by leaving them unpinned or setting some constraints.
However, to achieve :doc:`/guides/reproducible-builds`
it is better that you lock your dependencies,
so that the decision to upgrade any of them is yours.
Poetry does this using ``poetry.lock`` files
that contain the exact versions of all your transitive dependencies
(that is, all the dependencies of your dependencies).

The first time you run ``poetry install`` in your project directory
`Poetry will generate a new poetry.lock
file <https://python-poetry.org/docs/basic-usage/#installing-without-poetrylock>`_
with the versions available at that moment.
You can then `commit your poetry.lock to version
control <https://python-poetry.org/docs/basic-usage/#commit-your-poetrylock-file-to-version-control>`_
so that Read the Docs also uses these exact dependencies.
