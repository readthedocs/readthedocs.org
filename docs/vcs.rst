VCS Integration
===============

GitHub
------

If you want to integrate GitHub editing into your own theme, the following variables are available in your custom templates:

* github_user - GitHub username
* github_repo - GitHub repo name
* github_version - Github blob
* conf_py_path - Path in the checkout to the docs root
* pagename - Sphinx variable representing the name of the page you're on.
* display_github

It can be used like this::

      {% if display_github %}
        <li><a href="https://github.com/{{ github_user }}/{{ github_repo }}/blob/{{ github_version }}{{ conf_py_path }}{{ pagename }}.rst">
          Show on GitHub</a></li>
      {% endif %}

Bitbucket
---------

If you want to integrate Bitbucket editing into your own theme, the following variables are available in your custom templates:

* bitbucket_user - Bitbucket username
* bitbucket_repo - Bitbucket repo name
* bitbucket_version - BitBucket version
* conf_py_path - Path in the checkout to the docs root
* pagename - Sphinx variable representing the name of the page you're on.
* display_bitbucket

It can be used like this::

      {% if display_bitbucket %}
        <a href="https://bitbucket.org/{{ bitbucket_user }}/{{ bitbucket_repo }}/src/{{ bitbucket_version}}{{ conf_py_path }}{{ pagename }}.rst'" class="icon icon-bitbucket"> Edit on Bitbucket</a>
      {% endif %}


