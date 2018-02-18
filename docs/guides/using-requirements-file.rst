Read the Docs: Using a requirements file
========================================

The requirements file option is useful in the following scenarios:
 - You are using external packages, extensions, and themes that you need to include in your documentation project
 - You have enabled the install project in a virtual environment option, but your package's setup.py file is not in the root directory.
 - You have multiple python packages in your project and you wish to document them.

-----------------------------
Using a pip requirements file
-----------------------------

Creating the requirements file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You are using external packages, extensions, and themes that you need to include in your documentation project
---------------------------------------------------------------------------------------------------------------

Read the Docs supports adding specific functionality, and themes to tailor the behavior and appearance
of your project's documentation. This is done by specifying a list of the packages, extensions, themes, to be used,
and their versions, during the documentation build process.

For example, one can specify which version of *Sphinx* to use, which theme they would like to use,
what extensions they would like to add and so on.

To do this, one can create a list of requirements and save it in a requirements file.

Since *RTD* uses Python language to build the workflow which automatically converts and hosts your project's
documentation, and uses various python packages for this, the requirments file is the same as any standard python project.
Read the Docs installs them in a virtual environment using pip, the standard python package manager.

In-fact, it is helpful to think of your documentation on readthedocs as a sub-project written in python,
within your main project's repo.

To use the requirements file:
Create a text file with a sensible name in the root directory of your documentation directory. For example::

    docs/requirements.txt
    docs/requirements-docs.txt

This is a standard python requirements file. If you know how to use that, this is the same thing. If not, read on.
In this file, list all the packages (one package per line) that you require for building your documentation.
Make sure to specify their appropriate version.

For example, say you wish to only use Sphinx version 1.1.x and the sphinx_rtd_theme with a minimum version of 0.1.9.
You are also using external extensions, for example, the napolean extension, (make sure to specify them in
the extensions list in conf.py file), then your requirements file might look something like this:

::

	# <insert optional comment explaining why this package or version is a requirement>
	sphinx == 1.1.*
	sphinx_rtd_theme >= 0.1.9
	sphinxcontrib-napolean


You have enabled the install project in a virtual environment option, but your package's setup.py file is not in the root directory.
---------------------------------------------------------------------------------------------------------------------------------------
OR
--
You have multiple python packages in your project and you wish to document them.
--------------------------------------------------------------------------------

If you enable the option to install your project in a virtual environment, RTD automatically uses
your project's setup.py file to install the packages. For this to work, the ``setup.py`` file must be
in the root directory of your project.

However, if you want to place your packages at a different location from the project's root directory,
or your project has multiple python packages that you wish to document, then you can create a requirements file
and specify the relative paths to your packages inside that file.

For example, if you want to keep your python package in the ``src/python`` directory, located at the root of your project,
create a ``requirements.readthedocs.txt`` file in your project root pointing to this path.
Make sure that the path to the packages' root directory is relative to the path of the ``requirements.readthedocs.txt`` file.

So if the requirements file is at the project root::

    /requirements.readthedocs.txt

its content will be::

    /src/python/

If you want to put the requirements in the file::

    /requirements/readthedocs.txt

its contents will be::

    ../src/python/

Using the requirements file
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Now, once the requirements file has been created for either scenario;

- Login to your Read the Docs project ( you have to be admin of the project).
- Go to My Projects (using the drop-down arrow next to your username in the top right).
- From the list of your Read the Docs projects, click on the project you wish to modify.
- Click on the Admin button along the top row.
- Go to advanced settings.
- Enable the option ``Install your project inside a virtualenv using setup.py install``.
- In the ``Requirements File:`` text-box below that, specify the path of the requirements file you just created.
- The path should be relative to the root directory of the documentation project.

