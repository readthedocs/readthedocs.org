My Build is Using Too Many Resources
====================================

We limit build resources to make sure that users don't overwhelm our build systems.
If you are running into this issue,
there are a couple fixes that you might try.

.. note:: The current build limits can be found on our :doc:`/builds` page.

Reduce formats you're building
------------------------------

You can change the formats of docs that you're building with our YAML file's :ref:`yaml-config:Formats` option.

In particular, the ``htmlzip`` takes up a decent amount of memory and time,
so disabling that format might solve your problem.

Reduce documentation build dependencies
---------------------------------------

A lot of projects reuse their requirements file for their documentation builds.
If there are extra packages that you don't need for building docs,
you can create a custom requirements file just for documentation.
This should speed up your documentation builds,
as well as reduce your memory footprint.

Use pip when possible
---------------------

If you don't need ``conda`` to create your *documentation* environment,
consider using ``pip`` instead since ``conda`` could `require too much memory`_ to calculate the dependency tree
when using multiple channels.

.. _require too much memory: https://github.com/conda/conda/issues/5003>


.. tip::

   Even though your *project* environment is created with ``conda``, it may be not necessary for the *documentation* environment.
   That is, to build the documentation is probably that you need fewer Python packages than to use your library itself.
   So, in this case, you could use ``pip`` to install those fewer packages instead of creating a big environment with ``conda``.


Use system site-packages for pre-installed libs
-----------------------------------------------

There are a few libraries that Read the Docs has already installed (scipy, numpy, matplotlib, pandas, etc)
in the Docker image used to build your docs. You can check the updated list of pre-installed libraries in the `Docker image repository`_.

To use these pre-installed libraries and avoid consuming time re-downloading/compiling them,
you can use the :ref:`yaml-config:python.use_system_site_packages` option to have access to them.

.. _Docker image repository: https://github.com/rtfd/readthedocs-docker-images
