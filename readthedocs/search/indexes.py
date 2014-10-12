"""
Search indexing classes to index into Elasticsearch.

Django settings that should be defined:

    `ES_HOSTS`: A list of hosts where Elasticsearch lives. E.g.
                ['192.168.1.1:9200', '192.168.2.1:9200']

    `ES_DEFAULT_NUM_REPLICAS`: An integer of the number of replicas.

    `ES_DEFAULT_NUM_SHARDS`: An integer of the number of shards.


TODO: Handle page removal case in Page.

"""
import datetime

from elasticsearch import Elasticsearch, exceptions
from elasticsearch.helpers import bulk_index

from django.conf import settings


class Index(object):
    """
    Base class to define some common methods across indexes.
    """
    # The _index and _type define the URL path to Elasticsearch, e.g.:
    #   http://localhost:9200/{_index}/{_type}/_search
    _index = 'readthedocs'
    _type = None

    def __init__(self):
        self.es = Elasticsearch(settings.ES_HOSTS)

    def get_settings(self, settings_override=None):
        """
        Returns settings to be passed to ES create_index.

        If `settings_override` is provided, this will use `settings_override`
        to override the defaults defined here.

        """
        default_settings = {
            'number_of_replicas': settings.ES_DEFAULT_NUM_REPLICAS,
            'number_of_shards': settings.ES_DEFAULT_NUM_SHARDS,
            'refresh_interval': '5s',
            'store.compress.tv': True,
            'store.compress.stored': True,
            'analysis': self.get_analysis(),
        }
        if settings_override:
            default_settings.update(settings_override)

        return default_settings

    def get_analysis(self):
        """
        Returns the analysis dict to be used in settings for create_index.

        For languages that ES supports we define either the minimal or light
        stemming, which isn't as aggresive as the snowball stemmer. We also
        define the stopwords for that language.

        For all languages we've customized we're using the ICU plugin.

        """
        analyzers = {}
        filters = {}

        # The default is used for fields that need ICU but are composed of
        # many languages.
        analyzers['default_icu'] = {
            'type': 'custom',
            'tokenizer': 'icu_tokenizer',
            'filter': ['word_delimiter', 'icu_folding', 'icu_normalizer'],
        }

        # Customize the word_delimiter filter to set various options.
        filters['custom_word_delimiter'] = {
            'type': 'word_delimiter',
            'preserve_original': True,
        }

        return {
            'analyzer': analyzers,
            'filter': filters,
        }

    def timestamped_index(self):
        return '{0}-{1}'.format(
            self._index, datetime.datetime.now().strftime('%Y%m%d%H%M%S'))

    def create_index(self, index=None):
        """
        Creates index.

        This uses `get_settings` and `get_mappings` to define the index.

        """
        index = index or self._index
        body = {
            'settings': self.get_settings(),
        }
        self.es.indices.create(index=index, body=body)

    def put_mapping(self, index=None):
        index = index or self._index
        self.es.indices.put_mapping(index, self._type, self.get_mapping())

    def bulk_index(self, data, index=None, chunk_size=500, parent=None,
                   routing=None):
        """
        Given a list of documents, uses Elasticsearch bulk indexing.

        For each doc this calls `extract_document`, then indexes.

        `chunk_size` defaults to the elasticsearch lib's default. Override per
        your document size as needed.

        """
        index = index or self._index
        docs = []
        for d in data:
            source = self.extract_document(d)
            doc = {
                '_index': index,
                '_type': self._type,
                '_id': source['id'],
                '_source': source,
            }
            if parent:
                doc['_parent'] = parent
            if routing:
                doc['_routing'] = routing
            docs.append(doc)

        bulk_index(self.es, docs, chunk_size=chunk_size)

    def index_document(self, data, index=None, parent=None, routing=None):
        doc = self.extract_document(data)
        kwargs = {
            'index': index or self._index,
            'doc_type': self._type,
            'body': doc,
            'id': doc['id']
        }
        if parent:
            kwargs['parent'] = parent
        if routing:
            kwargs['routing'] = routing
        self.es.index(**kwargs)

    def get_mapping(self):
        """
        Returns the mapping for this _index and _type.
        """
        raise NotImplemented

    def extract_document(self, pk, obj):
        """
        Extracts the Elasticsearch document for this object instance.
        """
        raise NotImplemented

    def update_aliases(self, new_index, delete=True):
        """
        Points `_index` to `new_index` and deletes `_index` if delete=True.

        The ES `update_aliases` is atomic.
        """
        old_index = None

        # Get current alias, if any.
        try:
            aliases = self.es.indices.get_alias(name=self._index)
            if aliases and aliases.keys():
                old_index = aliases.keys()[0]
        except exceptions.NotFoundError:
            pass

        actions = []
        if old_index:
            actions.append({'remove': {'index': old_index,
                                       'alias': self._index}})
        actions.append({'add': {'index': new_index, 'alias': self._index}})

        self.es.indices.update_aliases(body={'actions': actions})

        # Delete old index if any and if specified.
        if delete and old_index:
            self.es.indices.delete(index=old_index)

    def search(self, body, **kwargs):
        return self.es.search(index=self._index, doc_type=self._type,
                              body=body, **kwargs)


class ProjectIndex(Index):

    _type = 'project'

    def get_mapping(self):
        mapping = {
            self._type: {
                # Disable _all field to reduce index size.
                '_all': {'enabled': False},
                # Add a boost field to enhance relevancy of a document.
                '_boost': {'name': '_boost', 'null_value': 1.0},
                'properties': {
                    'id': {'type': 'long'},
                    'name': {'type': 'string', 'analyzer': 'default_icu'},
                    'slug': {'type': 'string', 'index': 'not_analyzed'},
                    'description': {'type': 'string', 'analyzer': 'default_icu'},
                    'lang': {'type': 'string', 'index': 'not_analyzed'},
                    'tags': {'type': 'string', 'index': 'not_analyzed'},
                    'privacy': {'type': 'string', 'index': 'not_analyzed'},
                    'author': {
                        'type': 'string',
                        'analyzer': 'default_icu',
                        'fields': {
                            'raw': {
                                'type': 'string',
                                'index': 'not_analyzed',
                            },
                        },
                    },
                    'url': {'type': 'string', 'index': 'not_analyzed'},
                }
            }
        }

        return mapping

    def extract_document(self, data):
        doc = {}

        attrs = ('id', 'name', 'slug', 'description', 'lang', 'tags', 'author', 'url')
        for attr in attrs:
            doc[attr] = data.get(attr, '')

        # Add project boost.
        doc['_boost'] = data.get('_boost', 1.0)

        return doc


class PageIndex(Index):

    _type = 'page'
    _parent = 'project'

    def get_mapping(self):
        mapping = {
            self._type: {
                # Disable _all field to reduce index size.
                '_all': {'enabled': False},
                # Add a boost field to enhance relevancy of a document.
                '_boost': {'name': '_boost', 'null_value': 1.0},
                # Associate a page with a project.
                '_parent': {'type': self._parent},
                'properties': {
                    'id': {'type': 'string', 'index': 'not_analyzed'},
                    'sha': {'type': 'string', 'index': 'not_analyzed'},
                    'project': {'type': 'string', 'index': 'not_analyzed'},
                    'version': {'type': 'string', 'index': 'not_analyzed'},
                    'path': {'type': 'string', 'index': 'not_analyzed'},
                    'title': {'type': 'string', 'analyzer': 'default_icu'},
                    'headers': {'type': 'string', 'analyzer': 'default_icu'},
                    'content': {'type': 'string', 'analyzer': 'default_icu'},
                    'taxonomy': {'type': 'string', 'analyzer': 'not_analyzed'},
                    'commit': {'type': 'string', 'analyzer': 'not_analyzed'},
                }
            }
        }

        return mapping

    def extract_document(self, data):
        doc = {}

        attrs = ('id', 'project', 'title', 'headers', 'version', 'path', 'content', 'taxonomy')
        for attr in attrs:
            doc[attr] = data.get(attr, '')

        # Add page boost.
        doc['_boost'] = data.get('_boost', 1.0)

        return doc

class SectionIndex(Index):

    _type = 'section'
    _parent = 'page'

    def get_mapping(self):
        mapping = {
            self._type: {
                # Disable _all field to reduce index size.
                '_all': {'enabled': False},
                # Add a boost field to enhance relevancy of a document.
                '_boost': {'name': '_boost', 'null_value': 1.0},
                # Associate a section with a page.
                '_parent': {'type': self._parent},
                # 'suggest': {
                #     'foo, bar'
                #     'payload': {
                #         url
                #         pk
                #     }
                # }
                'properties': {
                    'id': {'type': 'string', 'index': 'not_analyzed'},
                    'project': {'type': 'string', 'index': 'not_analyzed'},
                    'version': {'type': 'string', 'index': 'not_analyzed'},
                    'path': {'type': 'string', 'index': 'not_analyzed'},
                    'page_id': {'type': 'string', 'index': 'not_analyzed'},
                    'title': {'type': 'string', 'analyzer': 'default_icu'},
                    'content': {'type': 'string', 'analyzer': 'default_icu'},
                    'commit': {'type': 'string', 'analyzer': 'not_analyzed'},
                    'blocks': {
                        'type': 'object',
                        'properties': {
                            'code': {
                                {'type': 'string', 'analyzer': 'default_icu'}
                            }
                        }
                    }
                }
            }
        }

        return mapping

    def extract_document(self, data):
        doc = {}

        attrs = ('id', 'project', 'title', 'page_id', 'version', 'path',
                 'content')
        for attr in attrs:
            doc[attr] = data.get(attr, '')

        # Add page boost.
        doc['_boost'] = data.get('_boost', 1.0)

        return doc
