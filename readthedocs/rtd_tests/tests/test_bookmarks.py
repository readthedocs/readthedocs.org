from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

import json

from bookmarks.models import Bookmark


class TestBookmarks(TestCase):
    fixtures = ['eric.json', 'test_data.json']

    def test_create_bookmark(self):
        self.client.login(username='eric', password='test')
        post_data = {
            "url": "http://docs.readthedocs.org/en/latest/faq.html",
        }

        resp = self.client.post(reverse('bookmarks_add'),
                                data=json.dumps(post_data),
                                content_type='application/json',
                                )
        self.assertEqual(resp.status_code, 201)

        bookmark = Bookmark.objects.get(url=post_data['url'])
        self.assertEqual(bookmark.user.username, 'eric')

    def test_delete_bookmark(self):
        self.client.login(username='eric', password='test')
        post_data = {
            "url": "http://docs.readthedocs.org/en/latest/faq.html",
        }

        eric = User.objects.get(username='eric')
        Bookmark.objects.create(url=post_data['url'], user=eric)

        resp = self.client.post(reverse('bookmarks_remove'),
                                data=json.dumps(post_data),
                                content_type='application/json',
                                )
        self.assertEqual(resp.status_code, 200)

        try:
            Bookmark.objects.get(url=post_data['url'])
        except Exception, e:
            self.assertEqual(e.message, 'Bookmark matching query does not exist.')
