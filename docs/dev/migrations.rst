Database migrations
===================

We use `Django migrations <https://docs.djangoproject.com/en/4.2/topics/migrations/>`__ to manage database schema changes,
and the `django-safemigrate <https://github.com/aspiredu/django-safemigrate>`__ package to ensure that migrations are run in a given order to avoid downtime.

To make sure that migrations don't cause downtime,
the following rules should be followed for each case.

Adding a new field
------------------

**When adding a new field to a model, it should be nullable.**
This way, the database can be migrated without downtime, and the field can be populated later.
Don't forget to make the field non-nullable in a separate migration after the data has been populated.
You can achieve this by following these steps:

#. Set the new field as ``null=True`` and ``blank=True`` in the model.

   .. code-block:: python

      class MyModel(models.Model):
          new_field = models.CharField(
              max_length=100, null=True, blank=True, default="default"
          )

#. Make sure that the field is always populated with a proper value in the new code,
   and the code handles the case where the field is null.

   .. code-block:: python

      if my_model.new_field in [None, "default"]:
          pass


      # If it's a boolean field, make sure that the null option is removed from the form.
      class MyModelForm(forms.ModelForm):
          def __init__(self, *args, **kwargs):
              super().__init__(*args, **kwargs)
              self.fields["new_field"].widget = forms.CheckboxInput()
              self.fields["new_field"].empty_value = False

#. Create the migration file (let's call this migration ``app 0001``),
   and mark it as ``Safe.before_deploy()``.

   .. code-block:: python

      from django.db import migrations, models
      from django_safemigrate import Safe


      class Migration(migrations.Migration):
          safe = Safe.before_deploy()

#. Create a data migration to populate all null values of the new field with a proper value (let's call this migration ``app 0002``),
   and mark it as ``Safe.after_deploy()``.

   .. code-block:: python

       from django.db import migrations


       def migrate(apps, schema_editor):
           MyModel = apps.get_model("app", "MyModel")
           MyModel.objects.filter(new_field=None).update(new_field="default")


       class Migration(migrations.Migration):
           safe = Safe.after_deploy()

           operations = [
               migrations.RunPython(migrate),
           ]

#. After the deploy has been completed, create a new migration to set the field as non-nullable (let's call this migration ``app 0003``).
   Run this migration on a new deploy, you can mark it as ``Safe.before_deploy()`` or ``Safe.always()``.
#. Remove any handling of the null case from the code.

At the end, the deploy should look like this:

- Deploy web-extra.
- Run ``django-admin safemigrate`` to run the migration ``app 0001``.
- Deploy the webs
- Run ``django-admin migrate`` to run the migration ``app 0002``.
- Create a new migration to set the field as non-nullable,
  and apply it on the next deploy.

Removing a field
----------------

**When removing a field from a model,
all usages of the field should be removed from the code before the field is removed from the model,
and the field should be nullable.**
You can achieve this by following these steps:

#. Remove all usages of the field from the code.
#. Set the field as ``null=True`` and ``blank=True`` in the model.

   .. code-block:: python

      class MyModel(models.Model):
          field_to_delete = models.CharField(max_length=100, null=True, blank=True)

#. Create the migration file (let's call this migration ``app 0001``),
   and mark it as ``Safe.before_deploy()``.

   .. code-block:: python

      from django.db import migrations, models
      from django_safemigrate import Safe


      class Migration(migrations.Migration):
          safe = Safe.before_deploy()

#. Create a migration to remove the field from the database (let's call this migration ``app 0002``),
   and mark it as ``Safe.after_deploy()``.

   .. code-block:: python

      from django.db import migrations, models
      from django_safemigrate import Safe


      class Migration(migrations.Migration):
          safe = Safe.after_deploy()

At the end, the deploy should look like this:

- Deploy web-extra.
- Run ``django-admin safemigrate`` to run the migration ``app 0001``.
- Deploy the webs
- Run ``django-admin migrate`` to run the migration ``app 0002``.
