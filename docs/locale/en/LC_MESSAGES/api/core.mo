��    "      ,  /   <      �     �               =     T     g     �     �  3   �     �  $   �  $     $   ;  �   `  w   
  z   �    �  '     R   8  :   �  ^   �  &   %     L     g  !   �  1   �  5   �  B   	     R	  =   p	  8   �	     �	     �	  z  �	     t     �     �     �     �     �     �       3        M  $   l  $   �  $   �  �   �  w   �  z   �    x  '   �  R   �  :     ^   A  &   �     �     �  !      1   "  5   T  B   �     �  =   �  8   )     b     k                                 "                                                      !                                             	                      
    :mod:`core.admin` :mod:`core.forms` :mod:`core.management.commands` :mod:`core.middleware` :mod:`core.models` :mod:`core.search_sites` :mod:`core.views` :mod:`core` A list of facet names for which to get facet counts A post-commit hook for github. A simple 404 handler so we get media A simple 500 handler so we get media Additional information about a User. Although this is a choice field, no choices need to be supplied. Instead, we just validate that the value is in the correct format for facet filtering (facet_name:value) Core views, including the main homepage, post-commit build hook, documentation and header rendering, and server errors. Custom management command to rebuild documentation for all projects on the site. Invoked via ``./manage.py update_repos``. Determining which URL to redirect to is done based on the kwargs passed to reverse(serve_docs, kwargs).  This function populates kwargs for the default docs for a project, and sets appropriate keys depending on whether request is for a subdomain URL, or a non-subdomain URL. Django admin interface for core models. For filtering searches on a facet, with validation for the format of facet values. Gets the line to put into commits to attribute the author. In settings.MIDDLEWARE_CLASSES, SingleVersionMiddleware must follow after SubdomainMiddleware. Limit the search to one or more models Redirect / to /en/latest/. Redirect /en/ to /en/latest/. Redirect /latest/ to /en/latest/. Redirect /page/file.html to /en/latest/file.html. Reset urlconf for requests for 'single_version' docs. Return kwargs used to reverse lookup a project's default docs URL. Returns a tuple (name, email) Supports fetching faceted results with a corresponding query. This is where custom ``manage.py`` commands are defined. `facets` `models` Project-Id-Version: readthedocs-docs
Report-Msgid-Bugs-To: 
POT-Creation-Date: 2014-03-01 22:07+0800
PO-Revision-Date: 2014-03-01 13:43+0000
Last-Translator: Eric Holscher <eric@ericholscher.com>
Language-Team: LANGUAGE <LL@li.org>
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
Language: en
Plural-Forms: nplurals=2; plural=(n != 1);
 :mod:`core.admin` :mod:`core.forms` :mod:`core.management.commands` :mod:`core.middleware` :mod:`core.models` :mod:`core.search_sites` :mod:`core.views` :mod:`core` A list of facet names for which to get facet counts A post-commit hook for github. A simple 404 handler so we get media A simple 500 handler so we get media Additional information about a User. Although this is a choice field, no choices need to be supplied. Instead, we just validate that the value is in the correct format for facet filtering (facet_name:value) Core views, including the main homepage, post-commit build hook, documentation and header rendering, and server errors. Custom management command to rebuild documentation for all projects on the site. Invoked via ``./manage.py update_repos``. Determining which URL to redirect to is done based on the kwargs passed to reverse(serve_docs, kwargs).  This function populates kwargs for the default docs for a project, and sets appropriate keys depending on whether request is for a subdomain URL, or a non-subdomain URL. Django admin interface for core models. For filtering searches on a facet, with validation for the format of facet values. Gets the line to put into commits to attribute the author. In settings.MIDDLEWARE_CLASSES, SingleVersionMiddleware must follow after SubdomainMiddleware. Limit the search to one or more models Redirect / to /en/latest/. Redirect /en/ to /en/latest/. Redirect /latest/ to /en/latest/. Redirect /page/file.html to /en/latest/file.html. Reset urlconf for requests for 'single_version' docs. Return kwargs used to reverse lookup a project's default docs URL. Returns a tuple (name, email) Supports fetching faceted results with a corresponding query. This is where custom ``manage.py`` commands are defined. `facets` `models` 