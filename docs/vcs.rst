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
        <li><a href="https://github.com/{{ github_user }}/{{ github_repo }}/edit/{{ github_version }}{{ conf_py_path }}{{ pagename }}.rst">
          Edit on GitHub</a></li>
      {% endif %}


