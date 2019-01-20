# -*- coding: utf-8 -*-

from __future__ import (
    division,
    print_function,
    unicode_literals,
)

from django.test import TestCase

from readthedocs.restapi.utils import get_delete_query


class TestRestApiUtils(TestCase):

    def test_get_delete_query_with_no_arguments(self):
        returned_query = get_delete_query()
        expected_query = {
            'query': {
                'bool': {
                    'must': [],
                },
            },
        }
        self.assertDictEqual(expected_query, returned_query)
    
    def test_get_delete_query_with_project_slug_only(self):
        returned_query = get_delete_query(project_slug='sample-project-slug')
        expected_query = {
            'query': {
                'bool': {
                    'must': [
                        {
                            'term': {
                                'project': 'sample-project-slug'
                            },
                        },
                    ],
                },
            },
        }

        self.assertDictEqual(expected_query, returned_query)

    def test_get_delete_query_with_version_slug(self):
        returned_query = get_delete_query(version_slug='sample-version-slug')
        expected_query = {
            'query': {
                'bool': {
                    'must': [
                        {
                            'term': {
                                'version': 'sample-version-slug'
                            },
                        },
                    ],
                },
            },
        }

        self.assertDictEqual(expected_query, returned_query)

    def test_get_delete_query_with_commit_and_project_slug(self):
        returned_query = get_delete_query(project_slug='test-slug', commit='test-commit')
        expected_query = {
            'query': {
                'bool': {
                    'must': [
                        {
                            'term': {
                                'project': 'test-slug'
                            },
                        },
                    ],
                    'must_not': {
                        'term': {
                            'commit': 'test-commit'
                        },
                    },
                },
            },
        }
