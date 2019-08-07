# -*- coding: utf-8 -*-

"""Lookup tables for builders and backends."""
from importlib import import_module

from django.conf import settings


# Managers
mkdocs = import_module(settings.MKDOCS_BACKEND)
sphinx = import_module(settings.SPHINX_BACKEND)

BUILDER_BY_NAME = {
    # Possible HTML Builders
    'sphinx': sphinx.HtmlBuilder,
    'sphinx_htmldir': sphinx.HtmlDirBuilder,
    'sphinx_singlehtml': sphinx.SingleHtmlBuilder,
    # Other Sphinx Builders
    'sphinx_pdf': sphinx.PdfBuilder,
    'sphinx_epub': sphinx.EpubBuilder,
    'sphinx_singlehtmllocalmedia': sphinx.LocalMediaBuilder,
    # Other markup
    'mkdocs': mkdocs.MkdocsHTML,
    'mkdocs_json': mkdocs.MkdocsJSON,
}


def get_builder_class(name):
    return BUILDER_BY_NAME[name]
