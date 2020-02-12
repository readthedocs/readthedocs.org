"""Project signals."""

import django.dispatch


before_vcs = django.dispatch.Signal(providing_args=['version', 'environmemt'])
after_vcs = django.dispatch.Signal(providing_args=['version'])

before_build = django.dispatch.Signal(providing_args=['version', 'environmemt'])
after_build = django.dispatch.Signal(providing_args=['version'])

project_import = django.dispatch.Signal(providing_args=['project'])

# Used to purge files from the CDN
files_changed = django.dispatch.Signal(providing_args=['project', 'files'])

# Used to force verify a domain (eg. for SSL cert issuance)
domain_verify = django.dispatch.Signal(providing_args=['domain'])
