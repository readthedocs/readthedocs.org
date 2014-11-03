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

    def __add_bookmark(self):
        post_data = {
            "project": self.project.slug,
            "version": 'latest',
            "page": "",
            "url": "",
        }

        response = self.client.post(
            reverse('bookmarks_add'),
            data=json.dumps(post_data),
            content_type="application/json"
        )

        self.assertEqual(json.loads(response.content)['added'], True)
        self.assertEqual(response.status_code, 201)
        return Bookmark.objects.get(pk=1)

    def test_add_bookmark(self):
        bookmark = self.__add_bookmark()
        self.assertEqual(bookmark.user, self.user)
        self.assertEqual(bookmark.project.slug, self.project.slug)
        self.assertEqual(Bookmark.objects.count(), 1)

    def test_delete_bookmark_with_get_renders_confirmation_page(self):
        self.__add_bookmark()
        response = self.client.get(
            reverse('bookmark_remove', kwargs={'bookmark_pk': '1'})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'You sure? O_o')

    def test_delete_bookmark_with_url(self):
        self.__add_bookmark()
        response = self.client.post(
            reverse('bookmark_remove', kwargs={'bookmark_pk': '1'})
        )
        self.assertRedirects(response, reverse('bookmark_list'))
        self.assertEqual(Bookmark.objects.count(), 0)

    def test_delete_bookmark_with_json(self):
        self.__add_bookmark()

        post_data = {
            "project": self.project.slug,
            "version": 'latest',
            "page": "",
            "url": "",
        }

        response = self.client.post(
            reverse('bookmark_remove_json'),
            data=json.dumps(post_data),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Bookmark.objects.count(), 0)

    def test_dont_delete_bookmarks_with_bad_json(self):
        self.__add_bookmark()
        post_data = {"project": self.project.slug}

        response = self.client.post(
            reverse('bookmark_remove_json'),
            data=json.dumps(post_data),
            content_type="application/json"
        )
        self.assertContains(response, 'Invalid parameters')
        self.assertEqual(Bookmark.objects.count(), 1)
