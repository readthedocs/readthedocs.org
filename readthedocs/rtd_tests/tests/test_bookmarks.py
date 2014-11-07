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

        self.assertEqual(response.status_code, 201)
        self.assertContains(response, 'added', status_code=201)
        return Bookmark.objects.get(pk=1)

    def test_add_bookmark_denies_get_requests(self):
        response = self.client.get(reverse('bookmarks_add'))
        self.assertEqual(response.status_code, 405)
        self.assertContains(response, 'error', status_code=405)

    def test_add_bookmark(self):
        bookmark = self.__add_bookmark()
        self.assertEqual(bookmark.user, self.user)
        self.assertEqual(bookmark.project.slug, self.project.slug)
        self.assertEqual(Bookmark.objects.count(), 1)

    def test_add_bookmark_fails_bad_data(self):
        post_data = {
            "project": 'fail', "version": 'fail', "page": "", "url": ""
        }
        response = self.client.post(
            reverse('bookmarks_add'),
            data=json.dumps(post_data),
            content_type="text/javascript"
        )

        self.assertEqual(response.status_code, 400)
        self.assertContains(response, 'error', status_code=400)

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
        post_data = {"bad project": self.project.slug}

        response = self.client.post(
            reverse('bookmark_remove_json'),
            data=json.dumps(post_data),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Bookmark.objects.count(), 1)
        self.assertContains(response, "Invalid parameters", status_code=400)

    def test_bookmark_exists_true_when_exists(self):
        bookmark = self.__add_bookmark()
        post_data = {
            'project': bookmark.project.slug,
            'version': bookmark.version.slug,
            'page': bookmark.page
        }

        response = self.client.post(
            reverse('bookmark_exists'),
            data=json.dumps(post_data),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(json.loads(response.content)['exists'])

    def test_bookmark_exists_404_when_does_not_exist(self):
        response = self.client.post(
            reverse('bookmark_exists'),
            data=json.dumps(
                {'project': 'dont-read-docs', 'version': '', 'page': ''}
            ),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(json.loads(response.content)['exists'])

    def test_bookmark_exists_forbids_GET(self):
        response = self.client.get(reverse('bookmark_exists'))
        self.assertEqual(response.status_code, 405)
        self.assertNotContains(response, 'exists', status_code=405)
