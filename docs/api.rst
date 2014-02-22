Read the Docs Public API
=========================

We have a limited public API that is available for you to get data out of the site. This page will only show a few of the basic parts, please file a ticket or ping us on IRC (#readthedocs on `Freenode (chat.freenode.net) <http://webchat.freenode.net>`_) if you have feature requests.

This document covers the read-only API provided. We have plans to create a read/write API, so that you can easily automate interactions with your project.

The API is written in Tastypie, which provides a nice ability to browse the API from your browser. If you go to http://readthedocs.org/api/v1/?format=json and just poke around, you should be able to figure out what is going on.

A basic API client using slumber
--------------------------------

You can use `Slumber <http://slumber.in/>`_ to build basic API wrappers in python. Here is a simple example of using slumber to interact with the RTD API::

    import slumber
    import json

    show_objs = True
    api = slumber.API(base_url='http://readthedocs.org/api/v1/')

    val = api.project.get(slug='pip')
    #val = api.project('pip').get()

    #val = api.build(49252).get()
    #val = api.build.get(project__slug='read-the-docs')

    #val = api.user.get(username='eric')

    #val = api.version('pip').get()
    #val = api.version('pip').get(slug='1.0.1')

    #val = api.version('pip').highest.get()
    #val = api.version('pip').highest('0.8').get()

    if show_objs:
        for obj in val['objects']:
            print json.dumps(obj, indent=4)
    else:
        print json.dumps(val, indent=4)

Example of adding a user to a project
-------------------------------------

::

    import slumber

    USERNAME = 'eric'
    PASSWORD = 'test'
    
    user_to_add = 'coleifer'
    project_slug = 'read-the-docs'

    api = slumber.API(base_url='http://readthedocs.org/api/v1/', authentication={'name': USERNAME, 'password': PASSWORD})

    project = api.project.get(slug=project_slug)
    user = api.user.get(username=user_to_add)
    project_objects = project['objects'][0]
    user_objects = user['objects'][0]

    data = {'users': project_objects['users'][:]}
    data['users'].append(user_objects['resource_uri'])

    print "Adding %s to %s" % (user_objects['username'], project_objects['slug'])
    api.project(project_objects['id']).put(data)

    project2 = api.project.get(slug=project_slug)
    project2_objects = project2['objects'][0]
    print "Before users: %s" % project_objects['users']
    print "After users: %s" % project2_objects['users']


API Endpoints
-------------

Feel free to use cURL and python to look at formatted json examples. You can also look at them in your browser, if it handles returned json.

::

    curl http://readthedocs.org/api/v1/project/pip/?format=json | python -m json.tool

Root
----
.. http:method:: GET /api/v1/

.. http:response:: Retrieve a list of resources.
   
   .. sourcecode:: js
  
      {
          "build": {
              "list_endpoint": "/api/v1/build/", 
              "schema": "/api/v1/build/schema/"
          }, 
          "file": {
              "list_endpoint": "/api/v1/file/", 
              "schema": "/api/v1/file/schema/"
          }, 
          "project": {
              "list_endpoint": "/api/v1/project/", 
              "schema": "/api/v1/project/schema/"
          }, 
          "user": {
              "list_endpoint": "/api/v1/user/", 
              "schema": "/api/v1/user/schema/"
          }, 
          "version": {
              "list_endpoint": "/api/v1/version/", 
              "schema": "/api/v1/version/schema/"
          }
      }
      
   :data string list_endpoint: API endpoint for resource.
   :data string schema: API endpoint for schema of resource.

Builds
------
.. http:method:: GET /api/v1/build/

.. http:response:: Retrieve a list of Builds.

   .. sourcecode:: js

      {
          "meta": {
              "limit": 20, 
              "next": "/api/v1/build/?limit=20&offset=20", 
              "offset": 0, 
              "previous": null, 
              "total_count": 86684
          }, 
          "objects": [BUILDS]
      }

   :data integer limit: Number of Builds returned.
   :data string next: URI for next set of Builds.
   :data integer offset: Current offset used for pagination.
   :data string previous: URI for previous set of Builds.
   :data integer total_count: Total number of Builds.
   :data array objects: Array of `Build`_ objects.


Build
-----
.. http:method:: GET /api/v1/build/{id}/

   :arg id: A Build id.

.. http:response:: Retrieve a single Build.

   .. sourcecode:: js

      {
          "date": "2012-03-12T19:58:29.307403", 
          "error": "SPHINX ERROR", 
          "id": "91207", 
          "output": "SPHINX OUTPUT", 
          "project": "/api/v1/project/2599/", 
          "resource_uri": "/api/v1/build/91207/", 
          "setup": "HEAD is now at cd00d00 Merge pull request #181 from Nagyman/solr_setup\n", 
          "setup_error": "", 
          "state": "finished", 
          "success": true, 
          "type": "html", 
          "version": "/api/v1/version/37405/"
      }


   :data string date: Date of Build.
   :data string error: Error from Sphinx build process.
   :data string id: Build id.
   :data string output: Output from Sphinx build process.
   :data string project: URI for Project of Build.
   :data string resource_uri: URI for Build.
   :data string setup: Setup output from Sphinx build process.
   :data string setup_error: Setup error from Sphinx build process.
   :data string state: "triggered", "building", or "finished"
   :data boolean success: Was build successful?
   :data string type: Build type ("html", "pdf", "man", or "epub")
   :data string version: URI for Version of Build.

Files
-----
.. http:method:: GET /api/v1/file/

.. http:response:: Retrieve a list of Files.

   .. sourcecode:: js

      {
          "meta": {
              "limit": 20, 
              "next": "/api/v1/file/?limit=20&offset=20", 
              "offset": 0, 
              "previous": null, 
              "total_count": 32084
          }, 
          "objects": [FILES]
      }


   :data integer limit: Number of Files returned.
   :data string next: URI for next set of Files.
   :data integer offset: Current offset used for pagination.
   :data string previous: URI for previous set of Files.
   :data integer total_count: Total number of Files.
   :data array objects: Array of `File`_ objects.

File
----
.. http:method:: GET /api/v1/file/{id}/

   :arg id: A File id.

.. http:response:: Retrieve a single File.

   .. sourcecode:: js

      {
          "absolute_url": "/docs/keystone/en/latest/search.html", 
          "id": "332692", 
          "name": "search.html", 
          "path": "search.html", 
          "project": {PROJECT},
          "resource_uri": "/api/v1/file/332692/"
        }


   :data string absolute_url: URI for actual file (not the File object from the API.)
   :data string id: File id.
   :data string name: Name of File.
   :data string path: Name of Path.
   :data object project: A `Project`_ object for the file's project.
   :data string resource_uri: URI for File object.

Projects
--------
.. http:method:: GET /api/v1/project/

.. http:response:: Retrieve a list of Projects.

   .. sourcecode:: js

      {
          "meta": {
              "limit": 20, 
              "next": "/api/v1/project/?limit=20&offset=20", 
              "offset": 0, 
              "previous": null, 
              "total_count": 2067
          }, 
          "objects": [PROJECTS]
      }


   :data integer limit: Number of Projects returned.
   :data string next: URI for next set of Projects.
   :data integer offset: Current offset used for pagination.
   :data string previous: URI for previous set of Projects.
   :data integer total_count: Total number of Projects.
   :data array objects: Array of `Project`_ objects.

   
Project
-------
.. http:method:: GET /api/v1/project/{id}

   :arg id: A Project id.

.. http:response:: Retrieve a single Project.

   .. sourcecode:: js

      {
          "absolute_url": "/projects/docs/", 
          "analytics_code": "", 
          "copyright": "", 
          "crate_url": "", 
          "default_branch": "", 
          "default_version": "latest", 
          "description": "Make docs.readthedocs.org work :D", 
          "django_packages_url": "", 
          "documentation_type": "sphinx", 
          "id": "2599", 
          "modified_date": "2012-03-12T19:59:09.130773", 
          "name": "docs", 
          "project_url": "", 
          "pub_date": "2012-02-19T18:10:56.582780", 
          "repo": "git://github.com/rtfd/readthedocs.org", 
          "repo_type": "git", 
          "requirements_file": "", 
          "resource_uri": "/api/v1/project/2599/", 
          "slug": "docs", 
          "subdomain": "http://docs.readthedocs.org/", 
          "suffix": ".rst", 
          "theme": "default", 
          "use_virtualenv": false, 
          "users": [
              "/api/v1/user/1/"
          ], 
          "version": ""
      }


   :data string absolute_url: URI for project (not the Project object from the API.)
   :data string analytics_code: Analytics tracking code.
   :data string copyright: Copyright
   :data string crate_url: Crate.io URI.
   :data string default_branch: Default branch.
   :data string default_version: Default version.
   :data string description: Description of project.
   :data string django_packages_url: Djangopackages.com URI.
   :data string documentation_type: Either "sphinx" or "sphinx_html". 
   :data string id: Project id.
   :data string modified_date: Last modified date.
   :data string name: Project name.
   :data string project_url: Project homepage.
   :data string pub_date: Last published date.
   :data string repo: URI for VCS repository.
   :data string repo_type: Type of VCS repository.
   :data string requirements_file: Pip requirements file for packages needed for building docs.
   :data string resource_uri: URI for Project.
   :data string slug: Slug.
   :data string subdomain: Subdomain.
   :data string suffix: File suffix of docfiles. (Usually ".rst".)
   :data string theme: Sphinx theme.
   :data boolean use_virtualenv: Build project in a virtualenv? (True or False)
   :data array users: Array of readthedocs.org user URIs for administrators of Project.
   :data string version: DEPRECATED. 


Users
-----
.. http:method:: GET /api/v1/user/

.. http:response:: Retrieve List of Users

   .. sourcecode:: js
   
      {
          "meta": {
              "limit": 20, 
              "next": "/api/v1/user/?limit=20&offset=20", 
              "offset": 0, 
              "previous": null, 
              "total_count": 3200
          }, 
          "objects": [USERS]
      }

   :data integer limit: Number of Users returned.
   :data string next: URI for next set of Users.
   :data integer offset: Current offset used for pagination.
   :data string previous: URI for previous set of Users.
   :data integer total_count: Total number of Users.
   :data array USERS: Array of `User`_ objects.
 
 
User
----
.. http:method:: GET /api/v1/user/{id}/

   :arg id: A User id.
   
.. http:response:: Retrieve a single User

   .. sourcecode:: js
   
      {
          "first_name": "", 
          "id": "1", 
          "last_login": "2010-10-28T13:38:13.022687", 
          "last_name": "", 
          "resource_uri": "/api/v1/user/1/", 
          "username": "testuser"
      }
      
   :data string first_name: First name.
   :data string id: User id.
   :data string last_login: Timestamp of last login.
   :data string last_name: Last name.
   :data string resource_uri: URI for this user.
   :data string username: User name.
   
 
Versions
--------
.. http:method:: GET /api/v1/version/

.. http:response:: Retrieve a list of Versions.

   .. sourcecode:: js

      {
          "meta": {
              "limit": 20, 
              "next": "/api/v1/version/?limit=20&offset=20", 
              "offset": 0, 
              "previous": null, 
              "total_count": 16437
          }, 
          "objects": [VERSIONS]
      }


   :data integer limit: Number of Versions returned.
   :data string next: URI for next set of Versions.
   :data integer offset: Current offset used for pagination.
   :data string previous: URI for previous set of Versions.
   :data integer total_count: Total number of Versions.
   :data array objects: Array of `Version`_ objects.


Version
-------
.. http:method:: GET /api/v1/version/{id}

   :arg id: A Version id.

.. http:response:: Retrieve a single Version.

   .. sourcecode:: js

      {
          "active": false, 
          "built": false, 
          "id": "12095", 
          "identifier": "remotes/origin/zip_importing", 
          "project": {PROJECT}, 
          "resource_uri": "/api/v1/version/12095/", 
          "slug": "zip_importing", 
          "uploaded": false, 
          "verbose_name": "zip_importing"
      }


   :data boolean active: Are we continuing to build docs for this version? 
   :data boolean built: Have docs been built for this version?
   :data string id: Version id.
   :data string identifier: Identifier of Version.
   :data object project: A `Project`_ object for the version's project.
   :data string resource_uri: URI for Version object.
   :data string slug: String that uniquely identifies a project
   :data boolean uploaded: Were docs uploaded? (As opposed to being build by Read the Docs.)
   :data string verbose_name: Usually the same as Slug.


Filtering Examples
------------------

Find Highest Version
~~~~~~~~~~~~~~~~~~~~
::

    http://readthedocs.org/api/v1/version/pip/highest/?format=json
    
.. http:method:: GET /api/v1/version/{id}/highest/

   :arg id: A Version id.

.. http:response:: Retrieve highest version.

   .. sourcecode:: js

      {
          "is_highest": true, 
          "project": "Version 1.0.1 of pip (5476)", 
          "slug": [
              "1.0.1"
          ], 
          "url": "/docs/pip/en/1.0.1/", 
          "version": "1.0.1"
      }


Compare Highest Version
~~~~~~~~~~~~~~~~~~~~~~~

This will allow you to compare whether a certain version is the highest version of a specific project. The below query should return a `'is_highest': false` in the returned dictionary.

::

    http://readthedocs.org/api/v1/version/pip/highest/0.8/?format=json 

.. http:method:: GET /api/v1/version/{id}/highest/{version}

   :arg id: A Version id.
   :arg version: A Version number or string.

.. http:response:: Retrieve highest version.

   .. sourcecode:: js

      {
          "is_highest": false, 
          "project": "Version 1.0.1 of pip (5476)", 
          "slug": [
              "1.0.1"
          ], 
          "url": "/docs/pip/en/1.0.1/", 
          "version": "1.0.1"
      }
 

File Search
~~~~~~~~~~~
::

    http://readthedocs.org/api/v1/file/search/?format=json&q=virtualenvwrapper
    
.. http:method:: GET /api/v1/file/search/?q={search_term}

   :arg search_term: Perform search with this term.

.. http:response:: Retrieve a list of File objects that contain the search term.

   .. sourcecode:: js
   
      {
          "objects": [
              {
                  "absolute_url": "/docs/python-guide/en/latest/scenarios/virtualenvs/index.html", 
                  "id": "375539", 
                  "name": "index.html", 
                  "path": "scenarios/virtualenvs/index.html", 
                  "project": {
                      "absolute_url": "/projects/python-guide/", 
                      "analytics_code": null, 
                      "copyright": "Unknown", 
                      "crate_url": "", 
                      "default_branch": "", 
                      "default_version": "latest", 
                      "description": "[WIP] Python best practices...", 
                      "django_packages_url": "", 
                      "documentation_type": "sphinx_htmldir", 
                      "id": "530", 
                      "modified_date": "2012-03-13T01:05:30.191496", 
                      "name": "python-guide", 
                      "project_url": "", 
                      "pub_date": "2011-03-20T19:40:03.599987", 
                      "repo": "git://github.com/kennethreitz/python-guide.git", 
                      "repo_type": "git", 
                      "requirements_file": "", 
                      "resource_uri": "/api/v1/project/530/", 
                      "slug": "python-guide", 
                      "subdomain": "http://python-guide.readthedocs.org/", 
                      "suffix": ".rst", 
                      "theme": "kr", 
                      "use_virtualenv": false, 
                      "users": [
                          "/api/v1/user/130/"
                      ], 
                      "version": ""
                  }, 
                  "resource_uri": "/api/v1/file/375539/", 
                  "text": "...<span class=\"highlighted\">virtualenvwrapper</span>\n..."
              },
              ...
          ]
      }

Anchor Search
~~~~~~~~~~~~~
::

    http://readthedocs.org/api/v1/file/anchor/?format=json&q=virtualenv

.. http:method:: GET /api/v1/file/anchor/?q={search_term}

   :arg search_term: Perform search of files containing anchor text with this term.

.. http:response:: Retrieve a list of absolute URIs for files that contain the search term.

   .. sourcecode:: js

      {
          "objects": [
              "http//django-fab-deploy.readthedocs.org/en/latest/...", 
              "http//dimagi-deployment-tools.readthedocs.org/en/...", 
              "http//openblock.readthedocs.org/en/latest/install/base_install.html#virtualenv", 
              ...
          ]
      }

Stats
-----

In the v2 of the api, there is the beginning of some stats endpoints.

Build Stats
~~~~~~~~~~~

::

    http://readthedocs.org/api/v2/stats/build_stats/?interval=hour

.. http:method:: GET /api/v2/stats/build_stats/?interval={interval}

   :arg interval: The interval to use to group the results by. Valid values include:
                  ``minute``, ``hour``, ``day``, ``week``, ``month``, ``quarter``, and ``year``.

.. http:response:: The number of builds grouped the provided interval.

   .. sourcecode:: js

      {
          "results": [
              {
                  "count": 10,
                  "when": 1347667200
              }, {
                  "count": 7,
                  "when": 1347670800
              }
          ]
      }