# Generated by Django 4.2.4 on 2023-08-10 21:03

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0103_alter_emailhook_project_alter_webhook_project"),
    ]

    operations = [
        migrations.AlterField(
            model_name="httpheader",
            name="value",
            field=models.CharField(max_length=4096),
        ),
    ]
