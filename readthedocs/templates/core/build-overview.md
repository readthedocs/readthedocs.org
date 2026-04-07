{% comment %}
Template used for generating the build overview page that is posted as a comment on the build PR.

Whitespaces and newlines are important in some places like lists and tables,
make sure to adjust the tags accordingly, as they introduce newlines.

Markdown inside <details> requires a blank line after </summary>.
{% endcomment %}
### Documentation build overview

> 📚 [{{ project.name }}](https://{{ PRODUCTION_DOMAIN }}{% url "projects_detail" project.slug %}) | 🛠️ Build [#{{ current_version_build.pk }}](https://{{ PRODUCTION_DOMAIN }}{% url "builds_detail" project.slug current_version_build.pk %}) | 📁 Comparing {{ current_version_build.commit }} against [{{ base_version.verbose_name }}]({{ base_version.get_absolute_url }}) ({{ base_version_build.commit }})

[<kbd> &nbsp; 🔍 Preview build &nbsp; </kbd>]({{ current_version.get_absolute_url }})

{% if diff.files %}{% if diff.should_auto_expand %}
<details open>
<summary>{{ diff.files|length }} files changed</summary>

{% for file in diff.added %}- ➕ [`{{ file.path }}`]({{ file.url }})
{% endfor %}{% for file in diff.modified %}- 📝 [`{{ file.path }}`]({{ file.url }})
{% endfor %}{% for file in diff.deleted %}- ➖ [`{{ file.path }}`]({{ file.url }})
{% endfor %}
</details>
{% else %}
<details>
<summary>{{ diff.files|length }} files changed{% if diff.added %} · ➕ {{ diff.added|length }} added{% endif %}{% if diff.modified %} · 📝 {{ diff.modified|length }} modified{% endif %}{% if diff.deleted %} · ➖ {{ diff.deleted|length }} deleted{% endif %}</summary>
{% if diff.added %}
➕ **Added**
{% for file in diff.added|slice:":10" %}- [`{{ file.path }}`]({{ file.url }})
{% endfor %}{% if diff.added|length > 10 %}- *and {{ diff.added|length|add:"-10" }} more...*
{% endif %}{% endif %}{% if diff.modified %}
📝 **Modified**
{% for file in diff.modified|slice:":10" %}- [`{{ file.path }}`]({{ file.url }})
{% endfor %}{% if diff.modified|length > 10 %}- *and {{ diff.modified|length|add:"-10" }} more...*
{% endif %}{% endif %}{% if diff.deleted %}
➖ **Deleted**
{% for file in diff.deleted|slice:":10" %}- [`{{ file.path }}`]({{ file.url }})
{% endfor %}{% if diff.deleted|length > 10 %}- *and {{ diff.deleted|length|add:"-10" }} more...*
{% endif %}{% endif %}
</details>
{% endif %}{% else %}
No files changed.
{% endif %}
