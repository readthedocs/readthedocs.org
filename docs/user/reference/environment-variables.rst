Environment variable reference
==============================

All :doc:`build processes </builds>` have the following environment variables automatically defined and available for each build step:

.. envvar:: READTHEDOCS

    Whether the build is running inside Read the Docs.

    :Default: ``True``

.. envvar:: READTHEDOCS_PRODUCTION_DOMAIN

    Domain where Read the Docs application/dashboard and API are running.

    :Example: ``readthedocs.org``
    :Example: ``readthedocs.com``
    :Example: ``app.readthedocs.org``
    :Example: ``app.readthedocs.com``
    :Example: ``devthedocs.org``
    :Example: ``devthedocs.com``

.. envvar:: READTHEDOCS_PROJECT

    The :term:`slug` of the project being built. For example, ``my-example-project``.

.. envvar:: READTHEDOCS_LANGUAGE

    The locale name, or the identifier for the locale, for the project being built.
    This value comes from the project's configured language code,
    which is in lowercase and uses a dash as a separator.

    :Example: ``en``
    :Example: ``it``
    :Example: ``de-at``
    :Example: ``es``
    :Example: ``pt-br``

.. envvar:: READTHEDOCS_VERSION

    The :term:`slug` of the version being built, such as ``latest``, ``stable``,
    or a branch name like ``feature-1234``. For :doc:`pull request builds </pull-requests>`,
    the value will be the pull request number.

.. envvar:: READTHEDOCS_VERSION_NAME

    The verbose name of the version being built, such as ``latest``, ``stable``,
    or a branch name like ``feature/1234``.

.. envvar:: READTHEDOCS_VERSION_TYPE

    The type of the version being built.

    :Example: ``branch``
    :Example: ``tag``
    :Example: ``external`` (for :doc:`pull request builds </pull-requests>`)
    :Example: ``unknown``

.. envvar:: READTHEDOCS_VIRTUALENV_PATH

    Path for the :doc:`virtualenv that was created for this build </builds>`.
    Only exists for builds using Virtualenv and not Conda.

    :Example: ``/home/docs/checkouts/readthedocs.org/user_builds/project/envs/version``

.. envvar:: READTHEDOCS_OUTPUT

    Base path for well-known output directories. Files in these directories will automatically be found, uploaded, and published.

    You need to concatenate an output format to this variable.
    Currently valid formats are ``html``, ``pdf``, ``htmlzip``, and ``epub``.
    (e.g. ``$READTHEDOCS_OUTPUT/html/`` or ``$READTHEDOCS_OUTPUT/pdf/``)
    You also need to create the directory before moving outputs into the destination.
    You can create it with the following command ``mkdir -p $READTHEDOCS_OUTPUT/html/``.
    Note that only ``html`` supports multiple files,
    the other formats should have one and only one file to be uploaded.

    .. seealso::

       :ref:`build-customization:where to put files`
          Information about using custom commands to generate output that will automatically be published once your build succeeds.

.. envvar:: READTHEDOCS_CANONICAL_URL

    Canonical base URL for the version that is built.
    If the project has configured a :doc:`custom domain </custom-domains>` (e.g. ``docs.example.com``) it will be used in the resulting canonical URL.
    Otherwise, your project's :ref:`default subdomain <default-subdomain>` will be used.

    The path for the language and version is appended to the domain, so the final canonical base URLs can look like the following examples:

    :Example: ``https://docs.example.com/en/latest/``
    :Example: ``https://docs.readthedocs.io/ja/stable/``
    :Example: ``https://example--17.org.readthedocs.build/fr/17/``

.. envvar:: READTHEDOCS_REPOSITORY_PATH

    Path where the repository was cloned.

    :Example: ``/home/docs/checkouts/readthedocs.org/user_builds/test-builds/checkouts/latest``

.. envvar:: READTHEDOCS_GIT_CLONE_URL

    URL for the remote source repository, from which the documentation is cloned.
    It could be HTTPS, SSH or any other URL scheme supported by Git.
    This is the same URL defined in your Project's :term:`dashboard` in :menuselection:`Admin --> Settings --> Repository URL`.

    :Example: ``https://github.com/readthedocs/readthedocs.org``
    :Example: ``git@github.com:readthedocs/readthedocs.org.git``

.. envvar:: READTHEDOCS_GIT_IDENTIFIER

    Contains the Git identifier that was *checked out* from the remote repository URL.
    Possible values are either a branch or tag name.

    :Example: ``v1.x``
    :Example: ``bugfix/docs-typo``
    :Example: ``feature/signup``
    :Example: ``update-readme``

    .. note::

       When building pull requests, this variable contains the numeric ID of the pull request,
       as we don't have access to the branch name.

.. envvar:: READTHEDOCS_GIT_COMMIT_HASH

    Git commit hash identifier checked out from the repository URL.

    :Example: ``1f94e04b7f596c309b7efab4e7630ed78e85a1f1``

.. seealso::

   :doc:`/environment-variables`
      General information about how environment variables are used in the build process.

   :doc:`/guides/environment-variables`
      Learn how to define your own custom environment variables, in addition to the pre-defined ones.
