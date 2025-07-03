{% comment %}
Template used for generating the build overview page that is posted as a comment on the build PR.

Whitespaces and newlines are important in some places like lists and tables,
make sure to adjust the tags accordingly, as they introduce newlines.
{% endcomment %}

#### [View documentation preview]({{ current_version.get_absolute_url }})

> 📚 [{{ project.name }}](https://{{ PRODUCTION_DOMAIN }}{% url "projects_detail" project.slug %}) | 🛠️ Build [#{{ current_version_build.pk }}](https://{{ PRODUCTION_DOMAIN }}{% url "builds_detail" project.slug current_version_build.pk %}) ({{ current_version_build.commit }}) | comparing [{{ base_version.verbose_name }}]({{ base_version.get_absolute_url }}) ({{ base_version_build.commit }})

{% if diff.files %}
<details>
<summary>Show files ({{ diff.files|length }}) | {{ diff.modified|length }} modified | {{ diff.added|length }} added | {{ diff.deleted|length }} deleted</summary>

| File | Status |
| --- | --- |
{% for file in diff.files %}| [{{ file.path }}]({{ file.url }}) | {{ file.status.emoji }} {{ file.status }} |
{% endfor %}

</details>
{% else %}
No files changed.
{% endif %}
