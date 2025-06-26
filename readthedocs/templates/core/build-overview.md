{% comment %}
Template used for generating the build overview page that is posted as a comment on the build PR.

Whitespaces and newlines are important in some places like lists and tables,
make sure to adjust the tags accordingly, as they introduce newlines.
{% endcomment %}
## Documentation build overview

> 📚 [{{ project.name }}](https://{{ PRODUCTION_DOMAIN }}{% url "projects_detail" project.slug %}) | 🛠️ build [#{{ current_version_build.pk }}](https://{{ PRODUCTION_DOMAIN }}{% url "builds_detail" project.slug current_version_build.pk %}) ({{ current_version_build.commit }}) | 🔍 [preview]({{ current_version.get_absolute_url }})

### Files changed

> Comparing with [{{ base_version.verbose_name }}]({{ base_version.get_absolute_url }}) ({{ base_version_build.commit }}). Click on [↩️]({{ base_version.get_absolute_url }}) to see the file in the base version.

{% if diff.files %}
{% for file in diff.files|slice:5 %}- {{ file.status.emoji }} [{{ file.path }}]({{ file.url }}) [↩️]({{ file.base_url }})
{% endfor %}

{% if diff.files|length > 5 %}
<details>
<summary>Show all {{ diff.files|length }} files</summary>

> 📝 {{ diff.modified|length }} file(s) modified | ➕ {{ diff.added|length }} file(s) added | ❌ {{ diff.deleted|length }} file(s) deleted

| File | Status |
| --- | --- |
{% for file in diff.files %}| [{{ file.path }}]({{ file.url }}) [↩️]({{ file.base_url }}) | {{ file.status.emoji }} {{ file.status }} |
{% endfor %}

</details>
{% endif %}
{% else %}
No files changed.
{% endif %}
