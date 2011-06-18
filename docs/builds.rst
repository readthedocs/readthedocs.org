The build process
=================

Understanding how Read the Docs builds your project will help you with debugging the problems you have with the site. It should also allow you to take advantage of certain things that happen during the build process.

The first step of the process is that we check out your code from the repository you have given us. If the code is already checked out, we update the copy to the branch that you have specified in your projects configuration.

Then we build the proper backend code for the type of documentation you've selected. Currently we only support Sphinx, but we are looking to expand this selection.

When we build your documentation, we run `sphinx-build -b html . _build/html`, where `html` would be replaced with the correct backend. We also create man pages and pdf's automatically based on your project.

Then these files are rsync'd across to our application servers from the build server. Once on the application servers, they are served from nginx and then cached in Varnish for a week. This varnish cache is pro-actively purged whenever a new version of your docs are built.

Changing behavior for Read the Docs
-----------------------------------

When RTD builds your project, it sets the ``READTHEDOCS`` environment variable to the string `True`. So within your Sphinx's conf.py file, you can vary the behavior based on this. For example::

    import os
    on_rtd = os.environ['READTHEDOCS'] == 'True'
    if on_rtd:
        html_theme = 'default'
    else:
        html_theme = 'nature'



