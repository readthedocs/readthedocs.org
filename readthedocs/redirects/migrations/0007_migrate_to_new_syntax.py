# Generated by Django 4.2.5 on 2023-12-07 15:32

from django.db import migrations


def forwards_func(apps, schema_editor):
    """
    Migrate redirects to the new modeling.

    Migrating the syntax of redirects is done outside the migration,
    since models from migrations don't have access to some methods
    required for the migration.
    """
    Redirect = apps.get_model("redirects", "Redirect")
    Project = apps.get_model("projects", "Project")

    # Enable all redirects.
    Redirect.objects.filter(enabled=None).update(enabled=True)

    # Rename Sphinx redirects.
    Redirect.objects.filter(redirect_type="sphinx_html").update(
        redirect_type="clean_url_to_html"
    )
    Redirect.objects.filter(redirect_type="sphinx_htmldir").update(
        redirect_type="html_to_clean_url"
    )

    # Set positions with the same order as updated_dt.
    for project in Project.objects.filter(redirects__isnull=False).distinct():
        for i, redirect_pk in enumerate(
            project.redirects.order_by("-update_dt").values_list("pk", flat=True).all()
        ):
            Redirect.objects.filter(pk=redirect_pk).update(position=i)


class Migration(migrations.Migration):
    dependencies = [
        ("redirects", "0006_add_new_fields"),
    ]

    operations = [
        migrations.RunPython(forwards_func),
    ]
