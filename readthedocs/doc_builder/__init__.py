from .backends import sphinx, mkdocs


loading = {
    # Possible HTML Builders
    'sphinx': sphinx.HtmlBuilder,
    'sphinx_htmldir': sphinx.HtmlDirBuilder,
    'sphinx_singlehtml': sphinx.SingleHtmlBuilder,
    # Other Sphinx Builders
    'sphinx_pdf': sphinx.PdfBuilder,
    'sphinx_epub': sphinx.EpubBuilder,
    'sphinx_search': sphinx.SearchBuilder,
    'sphinx_singlehtmllocalmedia': sphinx.LocalMediaBuilder,
    # Other markup
    'mkdocs': mkdocs.Builder,
}
