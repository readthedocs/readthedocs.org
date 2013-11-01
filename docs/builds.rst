The build process
=================

.. Keeping this for backwards compat


Changing behavior for Read the Docs
-----------------------------------

When RTD builds your project, it sets the ``READTHEDOCS`` environment variable to the string `True`. So within your Sphinx's conf.py file, you can vary the behavior based on this. For example::

    import os
    on_rtd = os.environ.get('READTHEDOCS', None) == 'True'
    if on_rtd:
        html_theme = 'default'
    else:
        html_theme = 'nature'

Deleting a stale or broken build environment
--------------------------------------------

RTD doesn't expose this in the UI, but it is possible to remove the build directory of your project. If you want to remove a build environment for your project, hit http://readthedocs.org/wipe/<project_slug>/<version_slug>/. You must be logged in to do this.

Packages installed in the build environment
-------------------------------------------

The build server does have a select number of C libraries installed, because they are used across a wide array of python projects. We can't install every C library out there, but we try and support the major ones. We currently have the following libraries installed:

    * Latex (texlive-full)
    * libevent (libevent-dev)
    * dvipng
    * graphviz
    * libxslt1.1
    * libxml2-dev

Understanding what's going on
-----------------------------

.. note:: Builds happen on a server using only the RTD Public API. There is no reason that you couldn't build your own independent builder that wrote into the RTD namespace. The only thing that is currently unsupported there is a saner way than uploading the processed files as a zip.

Understanding how Read the Docs builds your project will help you with debugging the problems you have with the site. It should also allow you to take advantage of certain things that happen during the build process.

The first step of the process is that we check out your code from the repository you have given us. If the code is already checked out, we update the copy to the branch that you have specified in your projects configuration.

Then we build the proper backend code for the type of documentation you've selected. Currently we only support Sphinx, but we are looking to expand this selection.

When we build your documentation, we run `sphinx-build -b html . _build/html`, where `html` would be replaced with the correct backend. We also create man pages and pdf's automatically based on your project.

Then these files are rsync'd across to our application servers from the build server. Once on the application servers, they are served from nginx and then cached in Varnish for a week. This Varnish cache is pro-actively purged whenever a new version of your docs are built.

An example in code::

    update_imported_docs(project, version)
    (ret, out, err) = build_docs(project=project, version=version,
                                 pdf=pdf, man=man, epub=epub, dash=dash,
                                 record=record, force=force)
    #This follows the builder workflow layed out below.
    purge_version(version, subdomain=True,
                    mainsite=True, cname=True)

Writing your own builder
------------------------

The documentation build system in RTD is made pluggable, so that you can build out your own backend. If you have a documentation format that isn't currently supported, you can add support by contributing a backend.

The :doc:`api/doc_builder` API explains the higher level parts of the API that you need to implement. A basic run goes something like this::

    backend = get_backend(project.documentation_type)
    if force:
        backend.force(version)
    backend.clean(version)
    backend.build(version)
    if success:
        backend.move(version)
