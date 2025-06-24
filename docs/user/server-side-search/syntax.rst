Search query syntax
===================

When searching on Read the Docs with :doc:`server side search </server-side-search/index>`,
you can use some parameters in your query
in order to search on given projects, versions, or to get more accurate results.

Parameters
----------

Parameters are in the form of ``name:value``,
they can appear anywhere in the query,
and depending on the parameter, you can use one or more of them.

Any other text that isn't a parameter will be part of the search query.
If you don't want your search term to be interpreted as a parameter,
you can escape it like ``project\:docs``.

.. note::

   Unknown parameters like ``foo:bar`` don't require escaping.

The available parameters are:

project
   Indicates the project and version to include results from
   (this doesn’t include subprojects or translations).
   If the version isn’t provided, the default version will be used.
   More than one parameter can be included.

   Examples:

   - ``project:docs test``
   - ``project:docs/latest test``
   - ``project:docs/stable project:dev test``

subprojects
   Include results from the given project and its subprojects.
   If the version isn't provided, the default version of all projects will be used.
   If a version is provided, all subprojects matching that version
   will be included, and if they don't have a version with that name,
   we use their default version.
   More than one parameter can be included.

   Examples:

   - ``subprojects:docs test``
   - ``subprojects:docs/latest test``
   - ``subprojects:docs/stable subprojects:dev test``

user
   Include results from projects the given user has access to.
   The only supported value is ``@me``,
   which is an alias for the current user.
   Only one parameter can be included.
   If duplicated, the last one will override the previous one.

   Examples:

   - ``user:@me test``

Permissions
~~~~~~~~~~~

If the user doesn’t have permission over one version,
or if the version doesn’t exist, we don’t include results from that version.

The API will return all the projects that were used in the final search,
with that information you can check which projects were used in the search.

Limitations
~~~~~~~~~~~

In order to keep our search usable for everyone,
you can search up to 100 projects at a time.
If the resulting query includes more than 100 projects,
they will be omitted from the final search.

This syntax is only available when using our search API V3
or when using the global search (https://app.readthedocs.org/search/).

Searching multiple versions of the same project isn't supported,
the last version will override the previous one.

Special queries
---------------

Read the Docs uses the `Simple Query String`_ feature from `Elasticsearch`_.
This means that as the search query becomes more complex,
the results yielded become more specific.

.. _Simple Query String: https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-simple-query-string-query.html#
.. _Elasticsearch: https://www.elastic.co/products/elasticsearch

Exact phrase search
~~~~~~~~~~~~~~~~~~~

If a query is wrapped in ``"`` (double quotes),
then only those results where the phrase is exactly matched will be returned.

Examples:

- ``"custom css"``
- ``"adding a subproject"``
- ``"when a 404 is returned"``

Prefix query
~~~~~~~~~~~~

``*`` (asterisk) at the end of any term signifies a prefix query.
It returns the results containing the words with the specific prefix.

Examples:

- ``test*``
- ``build*``

Fuzziness
~~~~~~~~~

``~N`` (tilde followed by a number) after a word indicates edit distance (fuzziness).
This type of query is helpful when the exact spelling of the keyword is unknown.
It returns results that contain terms similar to the search term.

Examples:

- ``doks~1``
- ``test~2``
- ``getter~2``

Words close to each other
~~~~~~~~~~~~~~~~~~~~~~~~~

``~N`` (tilde followed by a number) after a phrase can be used to match words that are near to each other.

Examples:

- ``"dashboard admin"~2``
- ``"single documentation"~1``
- ``"read the docs policy"~5``
