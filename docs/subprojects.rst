Subprojects
===========

We support the concept of Subprojects. If you add a subproject to a project,
that documentation will also be served under the parent project's subdomain
(this does not integrate the documentation for the projects together -- see
below for hints on making that work).

For example,
Kombu is a subproject of celery,
so you can access it on the `celery.readthedocs.io` domain:

http://celery.readthedocs.io/projects/kombu/en/latest/

This also works the same for CNAMEs:

http://docs.celeryproject.org/projects/kombu/en/latest/

You can add subprojects in the Admin section for your project.

Project/Subproject integration
------------------------------

It is possible to create a unified documentation site that links several projects
together, but requires some careful planning to do so. Here's what's involved
at the moment:

1. The core toctree in all of the projects should have the same structure so that
   the sidebar looks the same on all projects.
2. Use :mod:`intersphinx <sphinx:sphinx.ext.intersphinx>` to link between the
   sites and use standard sphinx references to refer between the projects.
3. The intersphinx links and the sidebar links should all point at
   'stable’ or ‘latest’ depending on what version the current build is creating.

To do all of this, you'll probably find it easier to dynamically generate your toctree
and your intersphinx links, sharing code between the projects. You may want to
refer to this toctree
`generator script <https://github.com/robotpy/robotpy-docs/blob/master/gensidebar.py>`_.

To keep the 'latest' and 'stable' versions straight, you can detect the version
of the current build in ``conf.py`` like so::

    # on_rtd is whether we are on readthedocs.org
    on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

    # This is used for linking and such so we link to the thing we're building
    rtd_version = os.environ.get('READTHEDOCS_VERSION', 'latest')
    if rtd_version not in ['stable', 'latest']:
        rtd_version = 'stable'

Then you can generate your intersphinx links in conf.py dynamically::

    intersphinx_mapping = {
      'robotpy': ('http://robotpy.readthedocs.io/en/%s/' % rtd_version, None),
      'wpilib': ('http://robotpy-wpilib.readthedocs.io/en/%s/' % rtd_version, None),
    }

You can use the same technique to vary the links in your sidebar generator
if you call the sidebar generator from ``conf.py``.

.. seealso:: For an example implementation of the unified setup described here, check out the
             documentation for the `RobotPy project <http://robotpy.readthedocs.io>`_
             and some of its `various <http://robotpy.readthedocs.io/projects/pynetworktables/>`_
             `subprojects <http://robotpy.readthedocs.io/projects/pyfrc/>`_. They all appear to be
             a single unified project, when they are in fact actually each are
             separate projects hosted in individual repositories on GitHub.
