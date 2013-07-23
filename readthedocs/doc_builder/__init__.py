from .backends import (
    sphinx,
    sphinx_epub,
    sphinx_htmldir,
    sphinx_websupport2,
    sphinx_man,
    sphinx_pdf,
    sphinx_dash,
)


loading = {'sphinx': sphinx.Builder,
           'sphinx_epub': sphinx_epub.Builder,
           'sphinx_htmldir': sphinx_htmldir.Builder,
           'sphinx_websupport2': sphinx_websupport2.Builder,
           'sphinx_man': sphinx_man.Builder,
           'sphinx_pdf': sphinx_pdf.Builder,
           'sphinx_dash': sphinx_dash.Builder,
           }
