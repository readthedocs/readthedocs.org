from rest_framework import serializers


class PageSearchSerializer(serializers.Serializer):
    title = serializers.CharField()
    headers = serializers.ListField()
    content = serializers.CharField()
    path = serializers.CharField()
