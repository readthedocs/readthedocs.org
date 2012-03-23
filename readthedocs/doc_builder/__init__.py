from .backends import (
    sphinx_epub,
    sphinx_html,
    sphinx_htmldir,
    sphinx_man,
    sphinx_pdf,
    )


loading = {'sphinx': sphinx_html.Builder,
           'sphinx_epub': sphinx_epub.Builder,
           'sphinx_htmldir': sphinx_htmldir.Builder,
           'sphinx_man': sphinx_man.Builder,
           'sphinx_pdf': sphinx_pdf.Builder,
           }
