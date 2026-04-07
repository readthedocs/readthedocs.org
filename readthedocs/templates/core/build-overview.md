{% comment %}
Template used for generating the build overview page that is posted as a comment on the build PR.

Whitespaces and newlines are important in some places like lists and tables,
make sure to adjust the tags accordingly, as they introduce newlines.
{% endcomment %}
### Documentation build overview

> 📚 [{{ project.name }}](https://{{ PRODUCTION_DOMAIN }}{% url "projects_detail" project.slug %}) | 🛠️ Build [#{{ current_version_build.pk }}](https://{{ PRODUCTION_DOMAIN }}{% url "builds_detail" project.slug current_version_build.pk %}) | 📁 Comparing {{ current_version_build.commit }} against [{{ base_version.verbose_name }}]({{ base_version.get_absolute_url }}) ({{ base_version_build.commit }})

[<kbd> &nbsp; 🔍 Preview build &nbsp; </kbd>]({{ current_version.get_absolute_url }})

{% if diff.files %}
<details{% if diff.should_auto_expand %} open{% endif %}>
<summary>Show files changed ({{ diff.files|length }} files in total): 📝 {{ diff.modified|length }} modified | ➕ {{ diff.added|length }} added | ➖ {{ diff.deleted|length }} deleted</summary>

| File | Status |
| --- | --- |
{% for file in diff.added %}| [{{ file.path }}]({{ file.url }}) | {{ file.status.emoji }} {{ file.status }} |
{% endfor %}{% if diff.added and diff.non_added %}| | |
{% endif %}{% for file in diff.non_added %}| [{{ file.path }}]({{ file.url }}) | {{ file.status.emoji }} {{ file.status }} |
{% endfor %}

</details>
{% else %}
No files changed.
{% endif %}
