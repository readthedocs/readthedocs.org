# -*- coding: utf-8 -*-
# from sphinx.builders.websupport

from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.util import copy_static_entry
from sphinx.util.console import bold
from sphinx.util.osutil import copyfile
from translator import UUIDTranslator
from websupport.backend import DjangoStorage, WebStorage

import os

def copy_media(app, exception):
    if app.builder.name != 'websupport2' or exception:
        return
    for file in ['websupport2.css', 'websupport2.js_t']:
        app.info(bold('Copying %s... ' % file), nonl=True)
        dest_dir = os.path.join(app.builder.outdir, '_static')
        dest = os.path.join(dest_dir, file)
        source = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), 
            '_static', 
            file
        )
        ctx = app.builder.globalcontext
        ctx['websupport2_base_url'] = app.builder.config.websupport2_base_url
        copy_static_entry(source, dest_dir, app.builder, ctx)
        #copyfile(source, dest)
        app.info('done')


class UUIDBuilder(StandaloneHTMLBuilder):
    """
    Builds documents for the web support package.
    """
    name = 'websupport2'
    versioning_method = 'commentable'
    storage = WebStorage()

    def init(self):
        StandaloneHTMLBuilder.init(self)

        # add our custom bits
        self.script_files.append('_static/websupport2.js')
        self.css_files.append('_static/websupport2.css')

    def init_translator_class(self):
        self.translator_class = UUIDTranslator

def setup(app):
    app.add_builder(UUIDBuilder)
    app.connect('build-finished', copy_media)
    app.add_config_value('websupport2_base_url', 'http://localhost:8000/websupport', 'html')