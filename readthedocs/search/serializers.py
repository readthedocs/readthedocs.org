import logging
from pprint import pformat

from rest_framework import serializers

log = logging.getLogger(__name__)


class PageSearchSerializer(serializers.Serializer):
    project = serializers.CharField()
    version = serializers.CharField()
    title = serializers.CharField()
    path = serializers.CharField()
    link = serializers.SerializerMethodField()
    highlight = serializers.SerializerMethodField()

    def get_link(self, obj):
        projects_url = self.context.get('projects_url')
        if projects_url:
            docs_url = projects_url[obj.project]
            return docs_url + obj.path

    def get_highlight(self, obj):
        highlight = getattr(obj.meta, 'highlight', None)
        if highlight:
            for num, result in enumerate(highlight.content):
                # Change results to turn newlines in highlight into periods
                # https://github.com/rtfd/readthedocs.org/issues/5168
                new_text = result.replace('\n', '. ')
                highlight.content[num] = new_text
                ret = highlight.to_dict()
                log.debug('API Search highlight: %s', pformat(ret))
                return ret
