# Generated by Django 1.9.13 on 2018-07-16 15:45
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("gold", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="golduser",
            old_name="last_4_digits",
            new_name="last_4_card_digits",
        ),
    ]
