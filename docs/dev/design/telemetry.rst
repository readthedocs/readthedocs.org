Collect data about builds
=========================

We may want to take some decisions in the future about deprecations and supported versions.
Right now we don't have data about the usage of packages and their versions on Read the Docs
to be able to make an informed decision.

.. contents::
   :local:
   :depth: 3

Tools
-----

Kibana:
   - https://www.elastic.co/kibana
   - We can import data from ES.
   - Cloud service provided by Elastic.
Superset:
   - https://superset.apache.org/
   - We can import data from several DBs (including postgres and ES).
   - Easy to setup locally, but doesn't look like there is cloud provider for it.
Metabase:
   - https://www.metabase.com/
   - We can import data from several DBs (including postgres).
   - Cloud service provided by Metabase.

Summary: We have several tools that can inspect data form a postgres DB,
and we also have ``Kibana`` that works *only* with ElasticSearch.
The data to be collected can be saved in a postgres or ES database.
Currently, we are making use of Metabase to get other information,
so it's probably the right choice for this task.

Data to be collected
--------------------

The following data can be collected after installing all dependencies.

Configuration file
~~~~~~~~~~~~~~~~~~

We are saving the config file in our database,
but to save some space we are saving it only if it's different than the one from a previous build
(if it's the same we save a reference to it).

The config file being saved isn't the original one used by the user,
but the result of merging it with its default values.

We may also want to have the original config file,
so we know which settings users are using.

PIP packages
~~~~~~~~~~~~

We can get a json with all and root dependencies with ``pip list``.
This will allow us to have the name of the packages and their versions used in the build.

.. code-block::

   $ pip list --pre --local --format json | jq
   # and
   $ pip list --pre --not-required --local --format json | jq
   [
      {
         "name": "requests-mock",
         "version": "1.8.0"
      },
      {
         "name": "requests-toolbelt",
         "version": "0.9.1"
      },
      {
         "name": "rstcheck",
         "version": "3.3.1"
      },
      {
         "name": "selectolax",
         "version": "0.2.10"
      },
      {
         "name": "slumber",
         "version": "0.7.1"
      },
      {
         "name": "sphinx-autobuild",
         "version": "2020.9.1"
      },
      {
         "name": "sphinx-hoverxref",
         "version": "0.5b1"
      },
   ]

With the ``--not-required`` option, pip will list only the root dependencies.

Conda packages
~~~~~~~~~~~~~~

We can get a json with all dependencies with ``conda list --json``.
That command gets all the root dependencies and their dependencies
(there is no way to list only the root dependencies),
so we may be collecting some noise, but we can use ``pip list`` as a secondary source.

.. code-block::

   $ conda list --json --name conda-env

   [
      {
         "base_url": "https://conda.anaconda.org/conda-forge",
         "build_number": 0,
         "build_string": "py_0",
         "channel": "conda-forge",
         "dist_name": "alabaster-0.7.12-py_0",
         "name": "alabaster",
         "platform": "noarch",
         "version": "0.7.12"
      },
      {
         "base_url": "https://conda.anaconda.org/conda-forge",
         "build_number": 0,
         "build_string": "pyh9f0ad1d_0",
         "channel": "conda-forge",
         "dist_name": "asn1crypto-1.4.0-pyh9f0ad1d_0",
         "name": "asn1crypto",
         "platform": "noarch",
         "version": "1.4.0"
      },
      {
         "base_url": "https://conda.anaconda.org/conda-forge",
         "build_number": 3,
         "build_string": "3",
         "channel": "conda-forge",
         "dist_name": "python-3.5.4-3",
         "name": "python",
         "platform": "linux-64",
         "version": "3.5.4"
      }
   ]

APT packages
~~~~~~~~~~~~

We can get the list from the config file,
or we can list the packages installed with ``dpkg --get-selections``.
That command would list all pre-installed packages as well, so we may be getting some noise.

.. code-block:: console

   $ dpkg --get-selections

   adduser                                         install
   apt                                             install
   base-files                                      install
   base-passwd                                     install
   bash                                            install
   binutils                                        install
   binutils-common:amd64                           install
   binutils-x86-64-linux-gnu                       install
   bsdutils                                        install
   build-essential                                 install

We can get the installed version with:

.. code-block:: console

   $ dpkg --status python3

   Package: python3
   Status: install ok installed
   Priority: optional
   Section: python
   Installed-Size: 189
   Maintainer: Ubuntu Developers <ubuntu-devel-discuss@lists.ubuntu.com>
   Architecture: amd64
   Multi-Arch: allowed
   Source: python3-defaults
   Version: 3.8.2-0ubuntu2
   Replaces: python3-minimal (<< 3.1.2-2)
   Provides: python3-profiler
   Depends: python3.8 (>= 3.8.2-1~), libpython3-stdlib (= 3.8.2-0ubuntu2)
   Pre-Depends: python3-minimal (= 3.8.2-0ubuntu2)
   Suggests: python3-doc (>= 3.8.2-0ubuntu2), python3-tk (>= 3.8.2-1~), python3-venv (>= 3.8.2-0ubuntu2)
   Description: interactive high-level object-oriented language (default python3 version)
   Python, the high-level, interactive object oriented language,
   includes an extensive class library with lots of goodies for
   network programming, system administration, sounds and graphics.
   .
   This package is a dependency package, which depends on Debian's default
   Python 3 version (currently v3.8).
   Homepage: https://www.python.org/
   Original-Maintainer: Matthias Klose <doko@debian.org>

Or with

.. code-block:: console

   $ apt-cache policy python3

   Installed: 3.8.2-0ubuntu2
   Candidate: 3.8.2-0ubuntu2
   Version table:
   *** 3.8.2-0ubuntu2 500
         500 http://archive.ubuntu.com/ubuntu focal/main amd64 Packages
         100 /var/lib/dpkg/status

Python
~~~~~~

We can get the Python version from the config file when using a Python environment,
and from the ``conda list`` output when using a Conda environment.

OS
~~

We can infer the OS version from the build image used in the config file,
but since it changes with time, we can get it from the OS itself:

.. code-block::

   $ lsb_release --description
   Description:    Ubuntu 18.04.5 LTS
   # or
   $ cat /etc/issue
   Ubuntu 18.04.5 LTS \n \l

Format
~~~~~~

The final information to be saved would consist of:

- organization: the organization id/slug
- project: the project id/slug
- version: the version id/slug
- build: the build id, date, length, status.
- user_config: Original user config file
- final_config: Final configuration used (merged with defaults)
- packages.pip: List of pip packages with name and version
- packages.conda: List of conda packages with name, channel, and version
- packages.apt: List of apt packages
- python: Python version used
- os: Operating system used

.. code-block:: json

   {
     "organization": {
       "id": 1,
       "slug": "org"
     },
     "project": {
       "id": 2,
       "slug": "docs"
     },
     "version": {
       "id": 1,
       "slug": "latest"
     },
     "build": {
       "id": 3,
       "date/start": "2021-04-20-...",
       "length": "00:06:34",
       "status": "normal",
       "success": true,
       "commit": "abcd1234"
     },
     "config": {
       "user": {},
       "final": {}
     },
     "packages": {
        "pip": [{
           "name": "sphinx",
           "version": "3.4.5"
        }],
        "pip_all": [
          {
             "name": "sphinx",
             "version": "3.4.5"
          },
          {
             "name": "docutils",
             "version": "0.16.0"
          }
        ],
        "conda": [{
           "name": "sphinx",
           "channel": "conda-forge",
           "version": "0.1"
        }],
        "apt": [{
           "name": "python3-dev",
           "version": "3.8.2-0ubuntu2"
        }],
     },
     "python": "3.7",
     "os": "ubuntu-18.04.5"
   }

Storage
-------

All this information can be collected after the build has finished,
and we can store it in a dedicated database (telemetry), using Django's models.

Since this information isn't sensitive,
we should be fine saving this data even if the project/version is deleted.
As we don't care about historical data,
we can save the information per-version and from their latest build only.
And delete old data if it grows too much.

Should we make heavy use of JSON fields?
Or try to avoid nesting structures as possible?
Like config.user/config.final vs user_config/final_config.
Or having several fields in our model instead of just one big json field?
