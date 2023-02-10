Environment variables
=====================

All :doc:`build processes </builds>` have the following environment variables automatically defined and available for each build step:

.. envvar:: READTHEDOCS

    Whether the build is running inside Read the Docs.

    :Default: ``True``

.. envvar:: READTHEDOCS_PROJECT

    The :term:`slug` of the project being built. For example, ``my-example-project``.

.. envvar:: READTHEDOCS_LANGUAGE

    The locale name, or the identifier for the locale, for the project being built.
    This value comes from the project's configured language.

    :Examples: ``en``, ``it``, ``de_AT``, ``es``, ``pt_BR``

.. envvar:: READTHEDOCS_VERSION

    The :term:`slug` of the version being built, such as ``latest``, ``stable``,
    or a branch name like ``feature-1234``. For :doc:`pull request builds </pull-requests>`,
    the value will be the pull request number.

.. envvar:: READTHEDOCS_VERSION_NAME

    The verbose name of the version being built, such as ``latest``, ``stable``,
    or a branch name like ``feature/1234``.

.. envvar:: READTHEDOCS_VERSION_TYPE

    The type of the version being built.

    :Values: ``branch``, ``tag``, ``external`` (for :doc:`pull request builds </pull-requests>`), or ``unknown``

.. envvar:: READTHEDOCS_VIRTUALENV_PATH

    Path for the :ref:`virtualenv that was created for this build <builds:Understanding what's going on>`.
    Only exists for builds using Virtualenv and not Conda.

    :Example: ``/home/docs/checkouts/readthedocs.org/user_builds/project/envs/version``

.. seealso::

   :doc:`/environment-variables`
      General information about how environment variables are used in the build process.

   :doc:`/guides/environment-variables`
      Learn how to define your own custom environment variables, in addition to the pre-defined ones.
