"""Provision Elastic Search"""

from __future__ import absolute_import
import logging

from django.core.management.base import BaseCommand

from readthedocs.search.indexes import Index, PageIndex, ProjectIndex, SectionIndex

log = logging.getLogger(__name__)


class Command(BaseCommand):

    help = __doc__

    def handle(self, *args, **options):
        """Provision new ES instance"""
        index = Index()
        index_name = index.timestamped_index()

        log.info("Creating indexes..")
        index.create_index(index_name)
        index.update_aliases(index_name)

        log.info("Updating mappings..")
        proj = ProjectIndex()
        proj.put_mapping()
        page = PageIndex()
        page.put_mapping()
        sec = SectionIndex()
        sec.put_mapping()
        log.info("Done!")
