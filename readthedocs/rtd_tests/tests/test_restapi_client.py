# -*- coding: utf-8 -*-
from __future__ import (
    absolute_import, unicode_literals)

from django.test import TestCase

from readthedocs.restapi.client import DrfJsonSerializer


class TestDrfJsonSerializer(TestCase):
    data = {
       'proper': 'json'
    }
    serialized_data = '{"proper":"json"}'

    def test_serializer_loads_json(self):
        serializer = DrfJsonSerializer()
        data = serializer.loads(self.serialized_data)
        self.assertDictEqual(data, self.data)

    def test_serializer_dumps_json(self):
        serializer = DrfJsonSerializer()
        serialized_data = serializer.dumps(self.data)
        self.assertJSONEqual(serialized_data, self.serialized_data)
