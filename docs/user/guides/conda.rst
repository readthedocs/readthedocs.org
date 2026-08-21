How to use Conda as your Python environment
===========================================

Read the Docs supports Conda as an environment management tool,
along with Virtualenv.
Conda support is useful for people who depend on C libraries,
and need them installed when building their documentation.

This work was funded by `Clinical Graphics`_ -- many thanks for their support of open source.

.. _Clinical Graphics: https://www.clinicalgraphics.com/

Activating conda
----------------

Conda support is available using a :doc:`../config-file/index`, see :ref:`config-file/v2:conda`.

Our Docker images use Miniconda, a minimal conda installer.
After specifying your project requirements using a conda ``environment.yml`` file,
Read the Docs will create the environment (using ``conda env create``)
and add the core dependencies needed to build the documentation.

Creating the ``environment.yml``
--------------------------------

There are several ways of `exporting a conda environment`_:

- ``conda env export`` will produce a complete list of all the packages installed in the environment
  with their exact versions. This is the best option to ensure reproducibility,
  but can create problems if done from a different operative system than the target machine,
  in our case Ubuntu Linux.
- ``conda env export --from-history`` will only include packages that were explicitly requested
  in the environment, excluding the transitive dependencies. This is the best option to maximize
  cross-platform compatibility, however it may include packages that are not needed to build your docs.
- And finally, you can also write it by hand. This allows you to pick exactly the packages needed to
  build your docs (which also results in faster builds) and overcomes some limitations in the conda
  exporting capabilities.

For example, using the second method for an existing environment:

.. code-block::

    $ conda activate rtd38
    (rtd38) $ conda env export --from-history | tee environment.yml
    name: rtd38
    channels:
      - defaults
      - conda-forge
    dependencies:
      - rasterio==1.2
      - python=3.8
      - pytorch-cpu=1.7
    prefix: /home/docs/.conda/envs/rtd38

Read the Docs will override the ``name`` and ``prefix`` of the environment when creating it,
so they can have any value, or not be present at all.

.. tip:: Bear in mind that ``rasterio==1.2`` (double ``==``) will install version ``1.2.0``,
   whereas ``python=3.8`` (single ``=``) will fetch the latest ``3.8.*`` version,
   which is ``3.8.8`` at the time of writing.

.. _this GitHub issue for discussion: https://github.com/readthedocs/readthedocs.org/issues/3829
.. _exporting a conda environment: https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#sharing-an-environment

Effective use of channels
-------------------------

Conda packages are usually hosted on https://anaconda.org/, a registration-free artifact archive
maintained by Anaconda Inc. Contrary to what happens with the Python Package Index,
different users can potentially host the same package in the same repository,
each of them using their own *channel*. Therefore, when installing a conda package,
conda also needs to know which channels to use, and which ones take precedence.

If not specified, conda will use ``defaults``, the channel maintained by Anaconda Inc.
and subject to `Anaconda Terms of Service`_. It contains well-tested versions of the most widely used
packages. However, some packages are not available on the ``defaults`` channel,
and even if they are, they might not be on their latest versions.

As an alternative, there are channels maintained by the community that have a broader selection
of packages and more up-to-date versions of them, the most popular one being ``conda-forge``.

To use the ``conda-forge`` channel when specifying your project dependencies, include it in the list
of ``channels`` in ``environment.yml``, and conda will rank them in order of appearance.
To maximize compatibility, we recommend putting ``conda-forge`` above ``defaults``:

.. code-block:: yaml

    name: rtd38
    channels:
      - conda-forge
      - defaults
    dependencies:
      - python=3.8
      # Rest of the dependencies

.. tip:: If you want to opt out the ``defaults`` channel completely, replace it by ``nodefaults``
   in the list of channels. See `the relevant conda docs`_ for more information.

.. _Anaconda Terms of Service: https://www.anaconda.com/terms-of-service
.. _the relevant conda docs: https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html?highlight=nodefaults#creating-an-environment-file-manually

Making builds faster with mamba
-------------------------------

One important thing to note is that, when enabling the ``conda-forge`` channel,
the conda dependency solver requires a large amount of RAM and long solve times.
This is `a known issue`_ due to the sheer amount of packages available in conda-forge.

As an alternative, you can instruct Read the Docs to use mamba_,
a drop-in replacement for conda that is much faster
and reduces the memory consumption of the dependency solving process.

To do that, add a ``.readthedocs.yaml`` :doc:`configuration file </config-file/v2>`
with these contents:

.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2

   build:
     os: "ubuntu-24.04"
     tools:
       python: "miniconda3-3.12-24.9"

   conda:
     environment: environment.yml

You can read more about the :ref:`config-file/v2:build.tools.python` configuration
in our documentation.

.. _mamba: https://github.com/mamba-org/mamba
.. _a known issue: https://www.anaconda.com/understanding-and-improving-condas-performance/

Mixing conda and pip packages
-----------------------------

There are valid reasons to use pip inside a conda environment: some dependency
might not be available yet as a conda package in any channel,
or you might want to avoid precompiled binaries entirely.
In either case, it is possible to specify the subset of packages
that will be installed with pip in the ``environment.yml`` file. For example:

.. code-block:: yaml

    name: rtd38
    channels:
      - conda-forge
      - defaults
    dependencies:
      - rasterio==1.2
      - python=3.8
      - pytorch-cpu=1.7
      - pip>=20.1  # pip is needed as dependency
      - pip:
        - black==20.8b1

The `conda developers recommend in their best practices`_ to install as many
requirements as possible with conda, then use pip to minimize possible conflicts
and interoperability issues.

.. warning:: Notice that ``conda env export --from-history`` does not include packages installed with pip,
   see `this conda issue`_ for discussion.

.. _conda developers recommend in their best practices: https://www.anaconda.com/blog/using-pip-in-a-conda-environment
.. _this conda issue: https://github.com/conda/conda/issues/9628

Compiling your project sources
------------------------------

If your project contains extension modules written in a compiled language (C, C++, FORTRAN)
or server-side JavaScript, you might need special tools to build it from source
that are not readily available on our Docker images,
such as a suitable compiler, CMake, Node.js, and others.

Luckily, conda is a language-agnostic package manager, and many of these development tools
are already packaged on ``conda-forge`` or more specialized channels.

For example, this conda environment contains the required dependencies to compile
`Slycot`_ on Read the Docs:

.. code-block:: yaml

    name: slycot38
    channels:
      - conda-forge
      - defaults
    dependencies:
      - python=3.8
      - cmake
      - numpy
      - compilers

.. _Slycot: https://github.com/python-control/Slycot

Troubleshooting
---------------

If you have problems on the environment creation phase,
either because the build runs out of memory or time
or because some conflicts are found,
you can try some of these mitigations:

- Reduce the number of channels in ``environment.yml``, even leaving ``conda-forge`` only
  and opting out of the defaults adding ``nodefaults``.
- Constrain the package versions as much as possible to reduce the solution space.
- :ref:`Use mamba <guides/conda:Making builds faster with mamba>`,
  an alternative package manager fully compatible with conda packages.
- And, if all else fails,
  :ref:`request more resources <guides/build-using-too-many-resources:Requests more resources>`.

Custom Installs
---------------

If you are running a custom installation of Read the Docs,
you will need the ``conda`` executable installed somewhere on your ``PATH``.
Because of the way ``conda`` works,
we can't safely install it as a normal dependency into the normal Python virtualenv.

.. warning:: Installing conda into a virtualenv will override the ``activate`` script,
             making it so you can't properly activate that virtualenv anymore.
