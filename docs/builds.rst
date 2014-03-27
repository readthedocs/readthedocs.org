Build Process
=============

Understanding what's going on
-----------------------------

Understanding how Read the Docs builds your project will help you with debugging the problems you have with the site. It should also allow you to take advantage of certain things that happen during the build process.

The first step of the process is that we check out your code from the repository you have given us. If the code is already checked out, we update the copy to the branch that you have specified in your projects configuration.

Then we build the proper backend code for the type of documentation you've selected.

If you have the *Use Virtualenv* option enabled, we will run ``setup.py install`` on your package, installing it into a virtual environment. You can also define additional packages to install with the *Requirements File* option.

When we build your documentation, we run `sphinx-build -b html . _build/html`, where `html` would be replaced with the correct backend. We also create man pages and pdf's automatically based on your project.

Then these files are copied across to our application servers from the build server. Once on the application servers, they are served from nginx. 

An example in code:

.. code-block:: python

    update_imported_docs(project, version)
    if project.use_virtualenv:
        run('python setup.py install')
        if project.requirements_file:
            run('pip install -r %s' % project.requirements_file)
    build_docs(version=version, pdf=pdf, man=man, epub=epub, dash=dash)
    copy_files(artifact_dir)
    

Builder Responsibility
----------------------

Builders have a very specific job.
They take the updated source code and generate the correct artifacts.
The code lives in ``self.version.project.checkout_path(self.version.slug)``.
The artifacts should end up in ``self.version.project.artifact_path(version=self.version.slug, type=self.type)``
Where ``type`` is the name of your builder.
All files that end up in the artifact directory should be in their final form.

Packages installed in the build environment
-------------------------------------------

The build server does have a select number of C libraries installed, because they are used across a wide array of python projects. We can't install every C library out there, but we try and support the major ones. We currently have the following libraries installed:

    * Latex (texlive-full)
    * libevent (libevent-dev)
    * dvipng
    * graphviz
    * libxslt1.1
    * libxml2-dev

Writing your own builder
------------------------

.. note:: Builds happen on a server using only the RTD Public API. There is no reason that you couldn't build your own independent builder that wrote into the RTD namespace. The only thing that is currently unsupported there is a saner way than uploading the processed files as a zip.

The documentation build system in RTD is made pluggable, so that you can build out your own backend. If you have a documentation format that isn't currently supported, you can add support by contributing a backend.

The :doc:`api/doc_builder` API explains the higher level parts of the API that you need to implement. A basic run goes something like this::

    backend = get_backend(project.documentation_type)
    if force:
        backend.force(version)
    backend.clean(version)
    backend.build(version)
    if success:
        backend.move(version)

Deleting a stale or broken build environment
--------------------------------------------

RTD doesn't expose this in the UI, but it is possible to remove the build directory of your project. If you want to remove a build environment for your project, hit http://readthedocs.org/wipe/<project_slug>/<version_slug>/. You must be logged in to do this.

