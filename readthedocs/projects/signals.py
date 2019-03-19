# -*- coding: utf-8 -*-

"""Project signals."""

import django.dispatch


before_vcs = django.dispatch.Signal(providing_args=['version'])
after_vcs = django.dispatch.Signal(providing_args=['version'])

before_build = django.dispatch.Signal(providing_args=['version'])
after_build = django.dispatch.Signal(providing_args=['version'])

project_import = django.dispatch.Signal(providing_args=['project'])

files_changed = django.dispatch.Signal(providing_args=['project', 'files'])

bulk_post_create = django.dispatch.Signal(providing_args=['instance_list', 'commit'])

bulk_post_delete = django.dispatch.Signal(providing_args=['instance_list', 'commit'])

# Used to force verify a domain (eg. for SSL cert issuance)
domain_verify = django.dispatch.Signal(providing_args=['domain'])
