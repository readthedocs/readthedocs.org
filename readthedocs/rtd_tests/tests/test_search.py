# -*- coding: utf-8 -*-
from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import json

from django.core.urlresolvers import reverse
from django.test import TestCase, RequestFactory
from mock import patch
from urllib3._collections import HTTPHeaderDict

from readthedocs.projects.models import Project
from readthedocs.rtd_tests.mocks.search_mock_responses import (
    search_project_response, search_file_response
)


class TestSearch(TestCase):
    fixtures = ['eric', 'test_data']

    def setUp(self):
        self.client.login(username='eric', password='test')
        self.pip = Project.objects.get(slug='pip')
        self.factory = RequestFactory()

    def perform_request_file_mock(self, method, url, params=None, body=None, timeout=None, ignore=()):
        """
        Elastic Search Urllib3HttpConnection mock for file search
        """
        headers = HTTPHeaderDict({
            'content-length': '893',
            'content-type': 'application/json; charset=UTF-8'
            })
        raw_data = search_file_response
        return 200, headers, raw_data

    def perform_request_project_mock(self, method, url, params=None, body=None, timeout=None, ignore=()):
        """
        Elastic Search Urllib3HttpConnection mock for project search
        """
        headers = HTTPHeaderDict({
            'content-length': '893',
            'content-type': 'application/json; charset=UTF-8'
        })
        raw_data = search_project_response
        return 200, headers, raw_data

    @patch(
        'elasticsearch.connection.http_urllib3.Urllib3HttpConnection.perform_request',
        side_effect=perform_request_project_mock
    )
    def test_search_project(self, perform_request_mock):
        """
        Tests the search view (by project) by mocking the perform request method
        of the elastic search module. Checks the query string provided
        to elastic search.
        """
        self.client.login(username='eric', password='test')
        r = self.client.get(
            reverse('search'),
            {'q': 'pip', 'type': 'project', 'project': None}
        )
        self.assertEqual(r.status_code, 200)
        response = perform_request_mock.call_args_list[0][0][3]
        query_dict = json.loads(response)
        self.assertIn('query', query_dict)
        self.assertDictEqual({
            'bool': {
                'should': [
                    {'match': {'name': {'query': 'pip', 'boost': 10}}},
                    {'match': {'description': {'query': 'pip'}}}
                ]
            }
        }, query_dict['query'])
        main_hit = r.context['results']['hits']['hits'][0]
        self.assertEqual(r.status_code, 200)
        self.assertEqual(main_hit['_type'], 'project')
        self.assertEqual(main_hit['_type'], 'project')
        self.assertEqual(main_hit['fields']['name'], 'Pip')
        self.assertEqual(main_hit['fields']['slug'], 'pip')

    @patch(
        'elasticsearch.connection.http_urllib3.Urllib3HttpConnection.perform_request',
        side_effect=perform_request_file_mock
    )
    def test_search_file(self, perform_request_mock):
        """
        Tests the search view (by file) by mocking the perform request method
        of the elastic search module. Checks the query string provided
        to elastic search.
        """
        self.client.login(username='eric', password='test')
        r = self.client.get(
            reverse('search'),
            {'q': 'capitolo', 'type': 'file'}
        )
        response = perform_request_mock.call_args_list[0][0][3]
        query_dict = json.loads(response)
        self.assertIn('query', query_dict)
        self.assertDictEqual({
            'bool': {
                'filter': [{'term': {'version': 'latest'}}],
                'should': [
                    {'match_phrase': {'title': {'query': 'capitolo', 'boost': 10, 'slop': 2}}},
                    {'match_phrase': {'headers': {'query': 'capitolo', 'boost': 5, 'slop': 3}}},
                    {'match_phrase': {'content': {'query': 'capitolo', 'slop': 5}}}
                ]
            }
        }, query_dict['query'])
        main_hit = r.context['results']['hits']['hits'][0]
        self.assertEqual(r.status_code, 200)
        self.assertEqual(main_hit['_type'], 'page')
        self.assertEqual(main_hit['fields']['project'], 'prova')
        self.assertEqual(main_hit['fields']['path'], '_docs/cap2')

    @patch(
        'elasticsearch.connection.http_urllib3.Urllib3HttpConnection.perform_request',
        side_effect=perform_request_file_mock
    )
    def test_search_in_project(self, perform_request_mock):
        """
        Tests the search view (by file) by mocking the perform request method
        of the elastic search module. Checks the query string provided
        to elastic search.
        """
        self.client.login(username='eric', password='test')
        r = self.client.get(
            '/projects/pip/search/',
            {'q': 'capitolo'}
        )
        response = perform_request_mock.call_args_list[0][0][3]
        query_dict = json.loads(response)
        self.assertDictEqual({
            'bool': {
                'should': [
                    {'match': {'title': {'boost': 10, 'query': 'capitolo'}}},
                    {'match': {'headers': {'boost': 5, 'query': 'capitolo'}}},
                    {'match': {'content': {'query': 'capitolo'}}}
                    ],
                'filter': [
                    {'term': {'project': 'pip'}},
                    {'term': {'version': 'latest'}}
                ]
            }
        }, query_dict['query'])
        main_hit = r.context['results']['hits']['hits'][0]
        self.assertEqual(r.status_code, 200)
        self.assertEqual(main_hit['_type'], 'page')
        self.assertEqual(main_hit['fields']['project'], 'prova')
        self.assertEqual(main_hit['fields']['path'], '_docs/cap2')
