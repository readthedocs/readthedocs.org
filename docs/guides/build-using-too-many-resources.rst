My Build is Using Too Many Resources
====================================

We limit build resources to make sure that users don't overwhelm our build systems.
If you are running into this issue,
there are a couple fixes that you might try.

.. note:: The current build limits can be found on our :doc:`/builds` page.

Reduce formats you're building
------------------------------

You can change the formats of docs that you're building with our :doc:`/config-file/index`,
see :ref:`config-file/v2:formats`.

In particular, the ``htmlzip`` takes up a decent amount of memory and time,
so disabling that format might solve your problem.

Reduce documentation build dependencies
---------------------------------------

A lot of projects reuse their requirements file for their documentation builds.
If there are extra packages that you don't need for building docs,
you can create a custom requirements file just for documentation.
This should speed up your documentation builds,
as well as reduce your memory footprint.

Use mamba instead of conda
--------------------------

If you need conda packages to build your documentation,
you can :ref:`use mamba as a drop-in replacement to conda <guides/conda:Making builds faster with mamba>`,
which requires less memory and is noticeably faster.

Document Python modules API statically
--------------------------------------

If you are installing a lot of Python dependencies just to document your Python modules API using ``sphinx.ext.autodoc``,
you can give a try to `sphinx-autoapi`_ Sphinx's extension instead which should produce the exact same output but running statically.
This could drastically reduce the memory and bandwidth required to build your docs.

.. _sphinx-autoapi: https://sphinx-autoapi.readthedocs.io/

Requests more resources
-----------------------

If you still have problems building your documentation,
we can increase build limits on a per-project basis,
sending an email to support@readthedocs.org providing a good reason why your documentation needs more resources.
