Better handling of docs URLs
============================

``proxito`` is the component of our code base in charge of serving documentation
to users and handling any other URLs from the user documentation domain.

The current implementation has some problems that are discussed in this document,
and an alternative implementation is proposed to solve those problems.

Goals
-----

* Simplifying our parsing logic for URLs
* Removing reserved paths and ambiguities from URLs
* Allow serving docs from a different prefix and subproject prefix.

Non-goals
---------

* Allowing fully arbitrary URL generation for projects,
  like changing the order of the elements or removing them.

Current implementation
----------------------

The current implementation is based on Django URLs
trying to match a pattern that looks like a single project, a versioned project,
or a subproject, this means that a couple of URLs are *reserved*,
and won't resolve to the correct file if it exists
(https://github.com/readthedocs/readthedocs.org/issues/8399, https://github.com/readthedocs/readthedocs.org/issues/2292),
this usually happens with single version projects.

And to support custom URLs we are hacking into Django's urlconf
to override it at runtime,
this doesn't allow us to implement custom URLs for subprojects easily
(https://github.com/readthedocs/readthedocs.org/pull/8327).

Alternative implementation
--------------------------

Instead of trying to map a URL to a view,
we first analyze the root project (given from the subdomain),
and based on that we map each part of the URL to the *current* project and version.

This will allow us to reuse this code in our unresolver
without the need to override the Django's urlconf at runtime,
or guessing a project only by the structure of its URL.

Terminology:

Root project
  The project from where the documentation
  is served (usually the parent project of a subproject or translation).
Current project
  The project that owns the current file being served
  (a subproject, a translation, etc).
Requested file
  The final path to the file that we need to serve from the current project.

Look up process
---------------

Proxito will process all documentation requests from a single *docs serve* view,
excluding ``/_`` URLs.

This view then will process the current URL using the root project as follows:

- Check if the root project has translations
  (the project itself is a translation if isn't a single version project),
  and the first part is a language code and the second is a version.

  - If the lang code doesn't match, we continue.
  - If the lang code matches, but the version doesn't, we return 404.

- Check if it has subprojects and the first part of the URL matches the subprojects prefix (``projects``),
  and if the second part of the URL matches a subproject alias.

  - If the subproject prefix or the alias don't match, we continue.
  - If they match, we try to match the rest of the URL for translations/versions and single versions
    (i.e, we don't search for subprojects) and we use the subproject as the new *root project*.

- Check if the project is a single version.
  Here we just try to serve the rest of the URL as the file.

- Check if the first part of the URL is ``page``,
  then this is a ``page`` redirect.
  Note that this is done after we have discarded the project being a single version
  project, since it doesn't makes sense to use that redirect with single version projects,
  and it could collide with the project having a ``page/`` directory.

- 404 if none of the above rules match.

Custom URLs
~~~~~~~~~~~

We are using custom URLs mainly to serve the documentation
from a different directory:

- deeplearning/nemo/user-guide/docs/$language/$version/$filename
- deeplearning/nemo/user-guide/docs/$language/$version/$filename
- deeplearning/frameworks/nvtx-plugins/user-guide/docs/$language/$version/$filename

We always keep the lang/version/filename order,
do we need/want to support changing this order?
Doesn't seem useful to do so.

So, what we need is have a way to specify a prefix only.
We would have a prefix used for translations and another one used for subprojects.
These prefixes will be set in the root project.

The look up order would be as follow:

- If the root project has a custom prefix, and the current URL matches that prefix,
  remove the prefix and follow the translations and single version look up process.
  We exclude subprojects from it, i.e, we don't check for ``{prefix}/projects``.
- If the root project has subprojects and a custom subprojects prefix (``projects`` by default),
  and if the current URL matches that prefix,
  and the next part of the URL matches a subproject alias,
  continue with the subproject look up process.

Examples
--------

The next examples are organized in the following way:

- First there is a list of the projects involved,
  with their available versions.
- The first project would be the root project.
- The other projects will be related to the root project
  (their relationship is given by their name).
- Next we will have a table of the requests,
  and their result.

Project with versions and translations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Projects:

- project (latest, 1.0)
- project-es (latest, 1.0)

Requests:

.. list-table::
   :header-rows: 1

   * - Request
     - Requested file
     - Current project
     - Note
   * - /en/latest/manual/index.html
     - /latest/manual/index.html
     - project
     -
   * - /en/1.0/manual/index.html
     - /1.0/manual/index.html
     - project
     -
   * - /en/1.0/404
     - 404
     - project
     - The file doesn't exist
   * - /en/2.0/manual/index.html
     - 404
     - project
     - The version doesn't exist
   * - /es/latest/manual/index.html
     - /latest/manual/index.html
     - project-es
     -
   * - /es/1.0/manual/index.html
     - /1.0/manual/index.html
     - project-es
     -
   * - /es/1.0/404
     - 404
     - project-es
     - The translation exist, but not the file
   * - /es/2.0/manual/index.html
     - 404
     - project-es
     - The translation exist, but not the version
   * - /pt/latest/manual/index.html
     - 404
     - project
     - The translation doesn't exist

Project with subprojects and translations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Projects:

- project (latest, 1.0)
- project-es (latest, 1.0)
- subproject (latest, 1.0)
- subproject-es (latest, 1.0)

.. list-table::
   :header-rows: 1

   * - Request
     - Requested file
     - Current project
     - Note
   * - /projects/subproject/en/latest/manual/index.html
     - /latest/manual/index.html
     - subproject
     -
   * - /projects/subproject/en/latest/404
     - 404
     - subproject
     - The subproject exists, but not the file
   * - /projects/subproject/en/2.x/manual/index.html
     - 404
     - subproject
     - The subproject exists, but not the version
   * - /projects/subproject/es/latest/manual/index.html
     - /latest/manual/index.html
     - subproject-es
     -
   * - /projects/subproject/br/latest/manual/index.html
     - 404
     - subproject
     - The subproject exists, but not the translation
   * - /projects/nothing/en/latest/manual/index.html
     - 404
     - project
     - The subproject doesn't exist
   * - /manual/index.html
     - 404
     - project
     -

Single version project with subprojects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Projects:

- project (latest)
- subproject (latest, 1.0)
- subproject-es (latest, 1.0)

.. list-table::
   :header-rows: 1

   * - Request
     - Requested file
     - Current project
     - Note
   * - /projects/subproject/en/latest/manual/index.html
     - /latest/manual/index.html
     - subproject
     -
   * - /projects/subproject/en/latest/404
     - 404
     - subproject
     - The subproject exists, but the file doesn't
   * - /projects/subproject/en/2.x/manual/index.html
     - 404
     - subproject
     - The subproject exists, but the version doesn't
   * - /projects/subproject/es/latest/manual/index.html
     - /latest/manual/index.html
     - subproject-es
     -
   * - /projects/subproject/br/latest/manual/index.html
     - 404
     - subproject
     - The subproject exists, but the translation doesn't
   * - /projects/nothing/en/latest/manual/index.html
     - 404
     - project
     - The subproject doesn't exist
   * - /manual/index.html
     - /latest/manual/index.html
     - project
     -
   * - /404
     - 404
     - project
     - The file doesn't exist
   * - /projects/index.html
     - /latest/projects/index.html
     - project
     - The project has a ``projects`` directory!
   * - /en/index.html
     - /latest/en/index.html
     - project
     - The project has an ``en`` directory!

Project with single version subprojects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Projects:

- project (latest, 1.0)
- project-es (latest, 1.0)
- subproject (latest)

.. list-table::
   :header-rows: 1

   * - Request
     - Requested file
     - Current project
     - Note
   * - /projects/subproject/manual/index.html
     - /latest/manual/index.html
     - subproject
     -
   * - /projects/subproject/en/latest/manual/index.html
     - 404
     - subproject
     - The subproject is single version
   * - /projects/subproject/404
     - 404
     - subproject
     - The subproject exists, but the file doesn't
   * - /projects/subproject/br/latest/manual/index.html
     - /latest/br/latest/manual/index.html
     - subproject
     - The subproject has a ``br`` directory!
   * - /projects/nothing/manual/index.html
     - 404
     - project
     - The subproject doesn't exist
   * - /en/latest/manual/index.html
     - /latest/manual/index.html
     - project
     -
   * - /404
     - 404
     - project
     -

Project with custom prefix
~~~~~~~~~~~~~~~~~~~~~~~~~~

- project (latest, 1.0)
- subproject (latest, 1.0)

``project`` has the ``prefix`` prefix, and ``sub`` subproject prefix.

.. list-table::
   :header-rows: 1

   * - Request
     - Requested file
     - Current project
     - Note
   * - /en/latest/manual/index.html
     - 404
     - project
     - The prefix doesn't match
   * - /prefix/en/latest/manual/index.html
     - /latest/manual/index.html
     - project
     -
   * - /projects/subproject/en/latest/manual/index.html
     - 404
     - project
     - The subproject prefix doesn't match
   * - /sub/subproject/en/latest/manual/index.html
     - /latest/manual/index.html
     - subproject
     -
   * - /sub/nothing/en/latest/manual/index.html
     - 404
     - project
     - The subproject doesn't exist

Project with custom subproject prefix (empty)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- project (latest, 1.0)
- subproject (latest, 1.0)

``project`` has the ``/`` subproject prefix,
this allow us to serve subprojects without using a prefix.

.. list-table::
   :header-rows: 1

   * - Request
     - Requested file
     - Current project
     - Note
   * - /en/latest/manual/index.html
     - /latest/manual/index.html
     - project
     -
   * - /projects/subproject/en/latest/manual/index.html
     - 404
     - project
     - The subproject prefix doesn't match
   * - /subproject/en/latest/manual/index.html
     - /latest/manual/index.html
     - subproject
     -
   * - /nothing/en/latest/manual/index.html
     - /latest/manual/index.html
     - project
     - The subproject/file doesn't exist

Implementation example
----------------------

This is a simplified version of the implementation,
there are some small optimizations and validations that will be in the
final implementation.

In the final implementation we will be using regular expressions to extract
the parts from the URL.

.. code-block:: python

   from readthedocs.projects.models import Project

   LANGUAGES = {"es", "en"}


   def pop_parts(path, n):
       if path[0] == "/":
           path = path[1:]
       parts = path.split("/", maxsplit=n)
       start, end = parts[:n], parts[n:]
       end = end[0] if end else ""
       return start, end


   def resolve(canonical_project: Project, path: str, check_subprojects=True):
       prefix = "/"
       if canonical_project.prefix:
           prefix = canonical_project.prefix
       subproject_prefix = "/projects"
       if canonical_project.subproject_prefix:
           subproject_prefix = canonical_project.subproject_prefix

       # Multiversion project.
       if path.startswith(prefix):
           new_path = path.removeprefix(prefix)
           parts, new_path = pop_parts(new_path, 2)
           language, version_slug = parts
           if not canonical_project.single_version and language in LANGUAGES:
               if canonical_project.language == language:
                   project = canonical_project
           else:
               project = canonical_project.translations.filter(language=language).first()
               if project:
                   version = project.versions.filter(slug=version_slug).first()
                   if version:
                       return project, version, new_path
                   return project, None, None

       # Subprojects.
       if check_subprojects and path.startswith(subproject_prefix):
           new_path = path.removeprefix(subproject_prefix)
           parts, new_path = pop_parts(new_path, 1)
           project_slug = parts[0]
           project = canonical_project.subprojects.filter(alias=project_slug).first()
           if project:
               return resolve(
                   canonical_project=project,
                   path=new_path,
                   check_subprojects=False,
               )

       # Single project.
       if path.startswith(prefix):
           new_path = path.removeprefix(prefix)
           if canonical_project.single_version:
               version = canonical_project.versions.filter(
                   slug=canonical_project.default_version
               ).first()
               if version:
                   return canonical_project, version, new_path
               return canonical_project, None, None

       return None, None, None


   def view(canonical_project, path):
       current_project, version, file = resolve(
           canonical_project=canonical_project,
           path=path,
       )
       if current_project and version:
           return serve(current_project, version, file)

       if current_project:
           return serve_404(current_project)

       return serve_404(canonical_project)


   def serve_404(project, version=None):
       pass


   def serve(project, version, file):
       pass


Performance
~~~~~~~~~~~

Performance is mainly driven by the number of database lookups.
There is an additional impact performing a regex lookup.

- A single version project:

  - ``/index.html``: 1, the version.
  - ``/projects/guides/index.html``: 2, the version and one additional lookup for a path that looks like a subproject.

- A multi version project:

  - ``/en/latest/index.html``: 1, the version.
  - ``/es/latest/index.html``: 2, the translation and the version.
  - ``/br/latest/index.html``: 1, the translation (it doesn't exist).

- A project with single version subprojects:

  - ``/projects/subproject/index.html``: 2, the subproject and its version.

- A project with multi version subprojects:

  - ``/projects/subproject/en/latest/index.html``: 2, the subproject and its version.
  - ``/projects/subproject/es/latest/index.html``: 3, the subproject, the translation, and its version.
  - ``/projects/subproject/br/latest/index.html``: 2, the subproject and the translation (it doesn't exist).

As seen, the number of database lookups are the minimal
required to get the current project and version,
this is a minimum of 1, and maximum of 3.

Questions
---------

- When using custom URLs,
  should we support changing the URLs
  that aren't related to doc serving?

  These are:

  - Health check
  - Proxied APIs
  - robots and sitemap
  - The ``page`` redirect

  This can be useful for people that proxy us from another path.

- Should we use the urlconf from the subproject when processing it?
  This is an URL like ``/projects/subproject/custom/prefix/en/latest/index.html``.

  I don't think that's useful, but it should be easy to support if needed.

- Should we support the page redirect when using a custom subproject prefix?
  This is ``/{prefix}/subproject/page/index.html``.
