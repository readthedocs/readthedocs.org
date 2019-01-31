# -*- coding: utf-8 -*-

"""Resync GitHub project for user."""

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from readthedocs.oauth.services import GitHubService


class Command(BaseCommand):

    help = __doc__

    def handle(self, *args, **options):
        if args:
            for slug in args:
                for service in GitHubService.for_user(
                    User.objects.get(
                        username=slug,
                    ),
                ):
                    service.sync()
