# Changelog

This document will track major changes in the project.

Also note, this document is a Markdown file. This is mainly to keep parity with GitHub, and also because we can.

## July 23, 2015


* Django 1.8 Support Merged

### Code Notes


- Updated Django from `1.6.11` to `1.8.3`.
- Removed South and ported the South migrations to Django's migration framework.
- Updated django-celery from `3.0.23` to `3.1.26` as django-celery 3.0.x does not support Django 1.8.
- Updated Celery from `3.0.24` to `3.1.18` because we had to update django-celery. We need to test this extensively and might need to think about using the new Celery API directly and dropping django-celery. See release notes: http://docs.celeryproject.org/en/latest/whatsnew-3.1.html
- Updated tastypie from `0.11.1` to current master (commit `1e1aff3dd4dcd21669e9c68bd7681253b286b856`) as 0.11.x is not compatible with Django 1.8. No surprises expected but we should ask for a proper release, see release notes: https://github.com/django-tastypie/django-tastypie/blob/master/docs/release_notes/v0.12.0.rst
- Updated django-oauth from `0.16.1` to `0.21.0`. No surprises expected, see release notes [in the docs](https://django-allauth.readthedocs.org/en/latest/changelog.html) and [finer grained in the repo](https://github.com/pennersr/django-allauth/blob/9123223f167959e4e5c4074408db068f725559d1/ChangeLog#L1-169)
- Updated django-guardian from `1.2.0` to `1.3.0` to gain Django 1.8 support. No surprises expected, see release notes: https://github.com/lukaszb/django-guardian/blob/devel/CHANGES
- Using `django-formtools` instead of removed `django.contrib.formtools` now. Based on the Django release notes, these modules are the same except of the package name.
- Updated pytest-django from `2.6.2` to `2.8.0`. No tests required, but running the testsuite :smile: 
- Updated psycopg2 from 2.4 to 2.4.6 as 2.4.5 is required by Django 1.8. No trouble expected as Django is the layer between us and psycopg2. Also it's only a minor version upgrade. Release notes: http://initd.org/psycopg/docs/news.html#what-s-new-in-psycopg-2-4-6
- Added `django.setup()` to `conf.py` to load django properly for doc builds.
- Added migrations for all apps with models in the `readthedocs/` directory

### Deployment Notes

After you have updated the code and installed the new dependencies, you need to run these commands on the server:

```bash
python manage.py migrate contenttypes
python manage.py migrate projects 0002 --fake
python manage.py migrate --fake-initial
```

Locally I had trouble in a test environment that pip did not update to the specified commit of tastypie. It might be required to use `pip install -U -r requirements/deploy.txt` during deployment.


### Development Update Notes

The readthedocs developers need to execute these commands when switching to this branch (or when this got merged into master):

- **Before updating** please make sure that all migrations are applied:

```bash
python manage.py syncdb
python manage.py migrate
```

- Update the codebase: `git pull`
- You need to update the requirements with `pip install -r requirements.txt`
- Now you need to fake the initial migrations:

```bash
python manage.py migrate contenttypes
python manage.py migrate projects 0002 --fake
python manage.py migrate --fake-initial
```
