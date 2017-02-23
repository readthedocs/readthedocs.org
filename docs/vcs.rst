Version Control System Integration
==================================

If you want to integrate editing into your own theme, you will have to declare 
few variables inside your configuration file ``conf.py`` in the ``'html_context'`` 
setting, for the template to use them. 

More information can be found on `Sphinx documentation`_.

.. _`Sphinx documentation`: http://www.sphinx-doc.org/en/1.5.2/config.html#confval-html_context

GitHub
------

If you want to integrate GitHub, you can put the following snippet into 
your ``conf.py``::

    html_context = {
        "display_github": True, # Integrate GitHub
        "github_user": "MyUserName", # Username
        "github_repo": "MyDoc", # Repo name
        "github_version": "master", # Version
        "conf_py_path": "/source/", # Path in the checkout to the docs root
    }

It can be used like this::

    {% if display_github %}
        <li><a href="https://github.com/{{ github_user }}/{{ github_repo }}
        /blob/{{ github_version }}{{ conf_py_path }}{{ pagename }}.rst">
        Show on GitHub</a></li>
    {% endif %}

Bitbucket
---------

If you want to integrate Bitbucket, you can put the following snippet into 
your ``conf.py``::

    html_context = {
        "display_bitbucket": True, # Integrate Bitbucket
        "bitbucket_user": "MyUserName", # Username
        "bitbucket_repo": "MyDoc", # Repo name
        "bitbucket_version": "master", # Version
        "conf_py_path": "/source/", # Path in the checkout to the docs root
    }

It can be used like this::

    {% if display_bitbucket %}
        <a href="https://bitbucket.org/{{ bitbucket_user }}/{{ bitbucket_repo }}
        /src/{{ bitbucket_version}}{{ conf_py_path }}{{ pagename }}.rst'" 
        class="icon icon-bitbucket"> Edit on Bitbucket</a>
    {% endif %}

Gitlab
------

If you want to integrate Gitlab, you can put the following snippet into 
your ``conf.py``::

    html_context = {
        "display_gitlab": True, # Integrate Gitlab
        "gitlab_user": "MyUserName", # Username
        "gitlab_repo": "MyDoc", # Repo name
        "gitlab_version": "master", # Version
        "conf_py_path": "/source/", # Path in the checkout to the docs root
    }

It can be used like this::

    {% if display_gitlab %}
        <a href="https://{{ gitlab_host|default("gitlab.com") }}/
        {{ gitlab_user }}/{{ gitlab_repo }}/blob/{{ gitlab_version }}
        {{ conf_py_path }}{{ pagename }}{{ suffix }}" class="fa fa-gitlab"> 
        Edit on GitLab</a>
    {% endif %}

Additional variables
--------------------

* ``'pagename'`` - Sphinx variable representing the name of the page you're on.
