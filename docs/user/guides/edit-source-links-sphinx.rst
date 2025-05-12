Adding "Edit Source" links on your Sphinx theme
===============================================

You can use define some Sphinx variables in the ``html_context`` to tell Read the Docs Sphinx theme
to display "Edit Source" links on each page.

More information can be found on `Sphinx documentation`_.

.. _`our Sphinx theme`: https://sphinx-rtd-theme.readthedocs.io/
.. _`Sphinx documentation`: https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-html_context

GitHub
------

If you want to integrate GitHub, these are the required variables to put into
your ``conf.py``::

    html_context = {
        "display_github": True, # Integrate GitHub
        "github_user": "MyUserName", # Username
        "github_repo": "MyDoc", # Repo name
        "github_version": "master", # Version
        "conf_py_path": "/source/", # Path in the checkout to the docs root
    }

They can be used like this::

    {% if display_github %}
        <li><a href="https://github.com/{{ github_user }}/{{ github_repo }}
        /blob/{{ github_version }}{{ conf_py_path }}{{ pagename }}.rst">
        Show on GitHub</a></li>
    {% endif %}

Bitbucket
---------

If you want to integrate Bitbucket, these are the required variables to put into
your ``conf.py``::

    html_context = {
        "display_bitbucket": True, # Integrate Bitbucket
        "bitbucket_user": "MyUserName", # Username
        "bitbucket_repo": "MyDoc", # Repo name
        "bitbucket_version": "master", # Version
        "conf_py_path": "/source/", # Path in the checkout to the docs root
    }

They can be used like this::

    {% if display_bitbucket %}
        <a href="https://bitbucket.org/{{ bitbucket_user }}/{{ bitbucket_repo }}
        /src/{{ bitbucket_version}}{{ conf_py_path }}{{ pagename }}.rst'"
        class="icon icon-bitbucket"> Edit on Bitbucket</a>
    {% endif %}

Gitlab
------

If you want to integrate Gitlab, these are the required variables to put into
your ``conf.py``::

    html_context = {
        "display_gitlab": True, # Integrate Gitlab
        "gitlab_user": "MyUserName", # Username
        "gitlab_repo": "MyDoc", # Repo name
        "gitlab_version": "master", # Version
        "conf_py_path": "/source/", # Path in the checkout to the docs root
    }

They can be used like this::

    {% if display_gitlab %}
        <a href="https://{{ gitlab_host|default("gitlab.com") }}/
        {{ gitlab_user }}/{{ gitlab_repo }}/blob/{{ gitlab_version }}
        {{ conf_py_path }}{{ pagename }}{{ suffix }}" class="fa fa-gitlab">
        Edit on GitLab</a>
    {% endif %}

Additional variables
--------------------

* ``'pagename'`` - Sphinx variable representing the name of the page you're on.



Other Hosting Platforms
------
To support custom or lesser-known repository hosting platforms (such as Gitea, Forgejo, or Codeberg), you can configure the `html_context` in your `conf.py` file using the following variables:

```
html_context = {
    "display_repo": True,             # Enable generic repo integration
    "repo_host": "codeberg.org",      # Host (e.g., gitea.example.com, codeberg.org)
    "repo_user": "MyUserName",        # Username or organization
    "repo_slug": "MyDoc",             # Repository name
    "repo_version": "main",           # Branch or tag name
    "conf_src_path": "/src/branch/",  # Path between repo and version (Gitea uses /src/branch/)
    "conf_py_path": "/docs/",         # Path to docs root in repository
    "suffix": ".rst",                 # File suffix, e.g. .rst or .md
}
```

You can then use it in your theme template like this:

```
{% if display_repo %}
    <a href="https://{{ repo_host }}/{{ repo_user }}/{{ repo_slug }}
    {{ conf_src_path }}{{ repo_version }}{{ conf_py_path }}{{ pagename }}{{ suffix }}"
    class="fa fa-git-alt">Edit Source</a>
{% endif %}
```

This generic method supports any Git-based repository that has a URL structure similar to:

```
https://<host>/<user>/<repo>/src/branch/<branch>/<path>
```


