from rtd_tests.base import WizardTestCase
from projects.models import Project


class TestBasicsForm(WizardTestCase):

    fixtures = ["eric"]
    wizard_class_slug = 'import_wizard_view'
    url = '/dashboard/import/manual/'

    def setUp(self):
        self.client.login(username='eric', password='test')
        self.step_data['basics'] = {
            'name': 'foobar',
            'repo': 'http://example.com/foobar',
            'repo_type': 'git',
        }

    def test_form_pass(self):
        '''Only submit the basics'''
        resp = self.post_step('basics')
        self.assertWizardResponse(resp)

        proj = Project.objects.get(name='foobar')
        self.assertIsNotNone(proj)
        for (key, val) in self.step_data['basics'].items():
            self.assertEqual(getattr(proj, key), val)
        self.assertEqual(proj.documentation_type, 'auto')

    def test_form_missing(self):
        '''Submit form with missing data, expect to get failures'''
        self.step_data['basics'] = {'advanced': True}
        resp = self.post_step('basics')
        self.assertWizardFailure(resp, 'name')
        self.assertWizardFailure(resp, 'repo_type')


class TestAdvancedForm(TestBasicsForm):

    def setUp(self):
        super(TestAdvancedForm, self).setUp()
        self.step_data['basics']['advanced'] = True
        self.step_data['extra'] = {
            'description': 'Describe foobar',
            'language': 'en',
            'documentation_type': 'sphinx',
        }
        self.step_data['advanced'] = {
            'default_version': 'latest',
            'privacy_level': 'public',
            'python_interpreter': 'python',
        }

    def test_form_pass(self):
        '''Test all forms pass validation'''
        resp = self.post_step('basics')
        self.assertWizardResponse(resp, 'extra')
        resp = self.post_step('extra')
        self.assertWizardResponse(resp, 'advanced')
        resp = self.post_step('advanced')
        self.assertWizardResponse(resp)

        proj = Project.objects.get(name='foobar')
        self.assertIsNotNone(proj)
        data = self.step_data['basics']
        del data['advanced']
        data.update(self.step_data['extra'])
        data.update(self.step_data['advanced'])
        for (key, val) in data.items():
            self.assertEqual(getattr(proj, key), val)

    def test_form_missing_extra(self):
        '''Submit extra form with missing data, expect to get failures'''
        # Remove extra data to trigger validation errors
        self.step_data['extra'] = {}

        resp = self.post_step('basics')
        self.assertWizardResponse(resp, 'extra')
        resp = self.post_step('extra')

        self.assertWizardFailure(resp, 'language')
        self.assertWizardFailure(resp, 'documentation_type')

    def test_form_missing_advanced(self):
        '''Submit advanced form with missing data, expect to get failures'''
        # Remove extra data to trigger validation errors
        self.step_data['advanced'] = {}

        resp = self.post_step('basics')
        self.assertWizardResponse(resp, 'extra')
        resp = self.post_step('extra')
        self.assertWizardResponse(resp, 'advanced')
        resp = self.post_step('advanced')

        self.assertWizardFailure(resp, 'default_version')
        self.assertWizardFailure(resp, 'privacy_level')
        self.assertWizardFailure(resp, 'python_interpreter')
