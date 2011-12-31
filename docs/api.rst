Read the Docs Public API
=========================

We have a limited public API that is available for you to get data out of the site. This page will only show a few of the basic parts, please file a ticket or ping us on IRC (#readthedocs on `Freenode (chat.freenode.net) <http://webchat.freenode.net>`_) if you have feature requests.

This document covers the read-only API provided. We have plans to create a read/write API, so that you can easily automate interactions with your project.

A basic API client using slumber
================================

You can use `Slumber <http://slumber.in/>`_ to build basic API wrappers in python. Here is a simple example of using slumber to interact with the RTD API::

    import slumber
    import json

    show_objs = True
    api = slumber.API(base_url='http://readthedocs.org/api/v1/')

    val = api.project.get(slug='pip')
    #val = api.project('pip').get()

    #val = api.build.get(pk=49252)
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
--------------------------------------

::

    import slumber

    USERNAME = 'eric'
    PASSWORD = 'test'
    
    user_to_add = 'coleifer'
    project = 'read-the-docs'

    api = slumber.API(base_url='http://readthedocs.org/api/v1/', authentication={'name': USERNAME, 'password': PASSWORD})

    project = api.project.get(slug=project)
    user = api.user.get(username=user_to_add)
    project_objects = project['objects'][0]
    user_objects = user['objects'][0]

    data = {'users': project_objects['users'][:]}
    data['users'].append(user_objects['resource_uri'])

    print "Adding %s to %s" % (user_objects['username'], project_objects['slug'])
    api.project(project_objects['id']).put(data)

    project2 = api.project.get(slug=project)
    project2_objects = project2['objects'][0]
    print "Before users: %s" % project_objects['users']
    print "After users: %s" % project2_objects['users']


API Examples
============

In all of these examples, replace `pip` with your own project.

Project Details
---------------

cURL
~~~~~
Feel free to use cURL and python to look at formatted json examples. You can also look at them in your browser, if it handles returned json.

`curl http://readthedocs.org/api/v1/project/pip/?format=json |python -mjson.tool`


URL
~~~
http://readthedocs.org/api/v1/project/pip/?format=json


Build List
----------

URL
~~~
http://readthedocs.org/api/v1/build/pip/?format=json

Version List
-------------

URL
~~~
http://readthedocs.org/api/v1/version/pip/?format=json


Highest Version
----------------

URL
~~~
http://readthedocs.org/api/v1/version/pip/highest/?format=json

Compare Highest Version
-----------------------

URL
~~~
http://readthedocs.org/api/v1/version/pip/highest/0.8/?format=json

This will allow you to compare whether a certain version is the highest version of a specific project. The above query should return a `'is_highest': false` in the returned dictionary.
