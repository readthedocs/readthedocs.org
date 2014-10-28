from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
import json

from projects.models import Project
from bookmarks.models import Bookmark

class TestBookmarks(TestCase):
    fixtures = ['eric', 'test_data']

    def setUp(self):
        self.project = Project.objects.get(pk=1)
        self.client.login(username='eric', password='test')
        self.user = User.objects.get(pk=1)
        self.project.users.add(self.user)

    def tearDown(self):
        pass

    def test_add_bookmark(self):
        post_data = {
            "project": self.project.slug,
            "version": 'latest',
            "page": "",
            "url": "",
        }

        response = self.client.post(reverse('bookmarks_add'),
                    data = json.dumps(post_data),
                    content_type = "application/json"
        )

        bookmark = Bookmark.objects.get(pk=1)
        self.assertEqual(bookmark.project.slug, self.project.slug)
        self.assertEqual(bookmark.user, self.user)
        self.assertEqual(response.status_code, 201)
