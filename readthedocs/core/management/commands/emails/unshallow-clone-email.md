[Action required] Unshallow your clone via the configuration file

{% load projects_tags %}
Some time ago we added an on-request "feature flag" to allow users to unshallow their Git repository
when clonning them as part of the build process.
With the introduction of the ability to [customize the build process](https://docs.readthedocs.io/en/latest/build-customization.html) via `build.jobs` and `build.commands`,
this feature flag is not required anymore and we are deprecating it.
Now, users have the ability to unshallow the Git repository clone without contacting support.

We are sending you this email because you are a maintainer of the following projects that have
this "feature flag" enabled and you should unshallow your clone now by using the configuration file:

{% spaceless %}
{% for project in projects %}
{% if project|has_feature:"dont_shallow_clone" %}
* [{{ production_uri }}{{ project.get_absolute_url }}]({{ project.slug }})
{% endif %}
{% endfor %}
{% endspaceless %}

Note this feature flag will be completely removed on **August 28th**.
Please, refer to [the example we have in the documentation](https://docs.readthedocs.io/en/latest/build-customization.html#unshallow-git-clone)
to unshallow your clone via the configuration file if your projects still require it.
