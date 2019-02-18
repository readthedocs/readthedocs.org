Conda Support
=============

.. warning:: This feature is in a beta state.
             Please file an `issue`_ if you find anything wrong.

Read the Docs supports Conda as an environment management tool,
along with Virtualenv.
Conda support is useful for people who depend on C libraries,
and need them installed when building their documentation.

This work was funded by `Clinical Graphics`_ -- many thanks for their support of Open Source.

Activating Conda
----------------

Conda support is avalible using a :doc:`config-file/index`, see :ref:`config-file/v2:conda`.

This Conda environment will also have Sphinx and other build time dependencies installed.
It will use the same order of operations that we support currently:

* Environment Creation (``conda env create``)
* Dependency Installation (Sphinx)

Custom Installs
---------------

If you are running a custom installation of Read the Docs,
you will need the ``conda`` executable installed somewhere on your ``PATH``.
Because of the way ``conda`` works,
we can't safely install it as a normal dependency into the normal Python virtualenv.

.. warning:: Installing conda into a virtualenv will override the ``activate`` script,
             making it so you can't properly activate that virtualenv anymore.

.. _issue: https://github.com/rtfd/readthedocs.org/issues
.. _Clinical Graphics: https://www.clinicalgraphics.com/
