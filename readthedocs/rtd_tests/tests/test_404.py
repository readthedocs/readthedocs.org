import lxml.html

from django.test import TestCase

from builds.models import Version
from projects.models import Project


class Testmaker(TestCase):
    fixtures = ["eric", "test_data"]

    def setUp(self):
        self.client.login(username='eric', password='test')
        self.pip = Project.objects.get(slug='pip')
        self.latest = Version.objects.create(project=self.pip, identifier='latest',
                               verbose_name='latest', slug='latest',
                               active=True)
        self.pip_es = Project.objects.create(name="PIP-ES", slug='pip-es', language='es', main_language_project=self.pip)

    def test_project_does_not_exist(self):
        # Case 1-4: Project doesn't exist
        r = self.client.get('/docs/nonexistent_proj/en/nonexistent_dir/subdir/bogus.html')
        self.assertContains(r, '''<p>We&#39;re sorry, we don&#39;t know what you&#39;re looking for</p>''', status_code=404, html=False)

    def test_only_project_exist(self):
        # Case 5: Project exists but both of version and language are not available
        r = self.client.get('/docs/pip/fr/nonexistent_ver/nonexistent_dir/bogus.html', {})
        self.assertContains(r, '<p>What are you looking for??</p>', status_code=404, html=False)

    def test_not_built_in_main_language(self):
        # Case 6: Project exists and main language is available but the version is not available
        r = self.client.get('/docs/pip/en/nonexistent_ver/nonexistent_dir/bogus.html', {})
        self.assertContains(r, '<p>Requested version seems not to have been built yet.', status_code=404, html=False)

    def test_not_built_in_other_language(self):
        # Case 6: Project exists and translation is available but the version is not available
        r = self.client.get('/docs/pip/es/nonexistent_ver/nonexistent_dir/bogus.html', {})
        self.assertContains(r, '<p>Requested version seems not to have been built yet.', status_code=404, html=False)

    def test_not_translated(self):
        # Case 7: Project exists and the version is available but not in the language
        r = self.client.get('/docs/pip/fr/latest/nonexistent_dir/bogus.html', {})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['X-Accel-Redirect'], '/user_builds/pip/translations/fr/latest/nonexistent_dir/bogus.html')
        r = self.client.get('/user_builds/pip/translations/fr/latest/nonexistent_dir/bogus.html', {})
        self.assertContains(r, '<p>Requested page seems not to be translated in requested language.', status_code=404, html=False)

    def test_no_dir_or_file_in_main_language(self):
        # Case 8: Everything is OK but sub-dir or file doesn't exist
        r = self.client.get('/docs/pip/en/latest/nonexistent_dir/bogus.html', {})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['X-Accel-Redirect'], '/user_builds/pip/rtd-builds/latest/nonexistent_dir/bogus.html')
        r = self.client.get('/user_builds/pip/rtd-builds/latest/nonexistent_dir/bogus.html', {})
        self.assertContains(r, '<p>What are you looking for?</p>', status_code=404, html=False)

    def test_no_dir_or_file_in_other_language(self):
        # Case 8: Everything is OK but sub-dir or file doesn't exist
        r = self.client.get('/docs/pip/es/latest/nonexistent_dir/bogus.html', {})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['X-Accel-Redirect'], '/user_builds/pip/translations/es/latest/nonexistent_dir/bogus.html')
        r = self.client.get('/user_builds/pip/translations/es/latest/nonexistent_dir/bogus.html', {})
        self.assertContains(r, '<p>What are you looking for?</p>', status_code=404, html=False)
