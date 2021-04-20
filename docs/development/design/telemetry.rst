Collect Data About Builds
=========================

We may want to take some decisions in the future about deprecations and supported versions.
Right now we don't have data about the usage of packages and their versions on Read the Docs
to be able to make a good decision.

.. contents::
   :local:
   :depth: 3

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
It's saved using a _fake_ ``JSONField``
(charfield that is transformed to json when creating the model object).
For these reasons we can't query or download them in bulk without iterating over all objects.

We may also want to have the original config file,
so we know which settings users are using.

PIP packages
~~~~~~~~~~~~

We can get a json with all root dependencies with ``pip list``.
This will allow us to have the name of the packages and their versions used in the build.

.. code-block::

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

Conda packages
~~~~~~~~~~~~~~

We can get a json with all dependencies with ``conda list --json``.
That command gets all the root dependencies and their dependencies,
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

This isn't implemented yet, but when it is,
we can get the list from the config file,
or we can list the packages installed with ``dpkg --get-selections``.
That command would list all pre-installed packages as well, so we may be getting some noise.

.. code-block::

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

Storage
-------

We can save all this information in json files in cloud storage,
then we could use a tool to import all this data into.
Or we can decide for a tool or service where to fed all this data directly into.

If we decide to save the files in cloud storage,
we can try to calculate a hash of the file so we don't upload duplicates that happen on the same day/month.
We can aggregate this data per year/month saving them in following structure:
``telemetry/builds/{year}/{month}/{year}-{month}-{day}-{timestamp-pk|pk}.json``,
that way is easy to download, all data per year/month without iterating over all files.

.. Since this information isn't sensitive,
   I think we are fine with this structure
   (we can't do bulk deletes of all info about a project if we follow this structure).

Format
~~~~~~

The final file to be saved would have the following information:

- project: the project slug
- version: the version slug
- build: the build id (which may stop existing if the project is deleted)
- date: full date in isoformat or timestamp (POSIX)
- user_config: Original user config file
- final_config: Final configuration used (merged with defaults)
- packages.pip: List of pip packages with name and version
- packages.conda: List of conda packages with name, channel, and version
- packages.apt: List of apt packages
- python: Python version used
- os: Operating system used

.. code-block:: json

   {
     "project": "docs",
     "version": "latest",
     "build": 12,
     "date": "2021-04-20-...",
     "user_config": {},
     "final_config": {},
     "packages": {
        "pip": [{
           "name": "sphinx",
           "version": "3.4.5"
        }],
        "conda": [{
           "name": "sphinx",
           "channel": "conda-forge",
           "version": "0.1"
        }],
        "apt": [
            "python3-dev",
            "cmatrix"
        ]
     },
     "python": "3.7",
     "os": {
         "name": "ubuntu",
         "version": "18.04.5"
     }
   }

Analyzing the data
------------------

.. How we would analyze this data? If we decide for a tool to fed the information into
   this wouldn't be a problem, but if we decide to go for storing the files for ourselves
   we can pick a tool later.
   Should we make this data public so other people can analyze it?
   Make it public after being analyzed and curated by us?
