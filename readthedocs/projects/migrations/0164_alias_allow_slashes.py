from django.core.validators import RegexValidator
from django.db import migrations
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.before_deploy()

    dependencies = [
        ("projects", "0163_automationrule_data_migration"),
    ]

    operations = [
        migrations.AlterField(
            model_name="projectrelationship",
            name="alias",
            field=models.CharField(
                blank=True,
                db_index=False,
                max_length=255,
                null=True,
                validators=[
                    RegexValidator(
                        message=_(
                            "Aliases must be slug-like segments separated by slashes "
                            "(e.g. 'api' or 'api/python')."
                        ),
                        regex=r"^[-\w]+(/[-\w]+)*$",
                    ),
                ],
                verbose_name=_("Alias"),
            ),
        ),
    ]
