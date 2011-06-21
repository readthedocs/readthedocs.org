from os.path import exists

from django.contrib.admin.models import User

from projects.models import Project
from rtd_tests.tests.base import RTDTestCase

from rtd_tests.utils import make_test_git


class TestBackend(RTDTestCase):
    fixtures = ['eric.json']

    def setUp(self):
        repo = make_test_git()
        super(TestBackend, self).setUp()
        self.eric = User.objects.get(username='eric')
        self.project = Project.objects.create(
            user=self.eric,
            name="Test Project",
            repo_type="git",
            #Our top-level checkout
            repo=repo
        )

    def test_parse_branches(self):
        data = """\
        develop
        master
        release/2.0.0
        rtd-jonas
        remotes/origin/2.0.X
        remotes/origin/HEAD -> origin/master
        remotes/origin/develop
        remotes/origin/master
        remotes/origin/release/2.0.0
        remotes/origin/release/2.1.0"""

        expected_ids = ['develop', 'master', 'release/2.0.0',
                        'rtd-jonas', 'remotes/origin/2.0.X',
                        'origin/master', 'remotes/origin/develop',
                        'remotes/origin/release/2.0.0',
                        'remotes/origin/release/2.1.0']
        given_ids = [x.identifier for x in
                     self.project.vcs_repo().parse_branches(data)]
        assert expected_ids == given_ids

    def test_git_checkout(self):
        repo = self.project.vcs_repo()
        repo.checkout()
        assert exists(repo.working_dir)
