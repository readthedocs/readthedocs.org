from os.path import exists

from django.contrib.admin.models import User

from projects.models import Project
from rtd_tests.tests.base import RTDTestCase

from rtd_tests.utils import make_test_git, make_test_hg


class TestGitBackend(RTDTestCase):
    fixtures = ['eric.json']

    def setUp(self):
        git_repo = make_test_git()
        super(TestGitBackend, self).setUp()
        self.eric = User.objects.get(username='eric')
        self.project = Project.objects.create(
            name="Test Project",
            repo_type="git",
            #Our top-level checkout
            repo=git_repo
        )
        self.project.users.add(self.eric)

    def test_parse_branches(self):
        data = """
        develop
        master
        release/2.0.0
        origin/2.0.X
        origin/HEAD -> origin/master
        origin/master
        origin/release/2.0.0
        """

        expected_ids = [
            ('develop', 'develop'), 
            ('master', 'master'),
            ('release/2.0.0', 'release-2.0.0'),
            ('origin/2.0.X', '2.0.X'),
            ('origin/master', 'master'),
            ('origin/release/2.0.0', 'release-2.0.0')
        ]
        given_ids = [(x.identifier, x.verbose_name) for x in
                     self.project.vcs_repo().parse_branches(data)]
        assert expected_ids == given_ids

    def test_git_checkout(self):
        repo = self.project.vcs_repo()
        repo.checkout()
        assert exists(repo.working_dir)

    def test_parse_git_tags(self):
        data = """\
            3b32886c8d3cb815df3793b3937b2e91d0fb00f1 refs/tags/2.0.0
            bd533a768ff661991a689d3758fcfe72f455435d refs/tags/2.0.1
            c0288a17899b2c6818f74e3a90b77e2a1779f96a refs/tags/2.0.2
            a63a2de628a3ce89034b7d1a5ca5e8159534eef0 refs/tags/2.1.0.beta2
            c7fc3d16ed9dc0b19f0d27583ca661a64562d21e refs/tags/2.1.0.rc1
            edc0a2d02a0cc8eae8b67a3a275f65cd126c05b1 refs/tags/2.1.0.rc2
         """
        expected_tags = [
            ('3b32886c8d3cb815df3793b3937b2e91d0fb00f1', '2.0.0'),
            ('bd533a768ff661991a689d3758fcfe72f455435d', '2.0.1'),
            ('c0288a17899b2c6818f74e3a90b77e2a1779f96a', '2.0.2'),
            ('a63a2de628a3ce89034b7d1a5ca5e8159534eef0', '2.1.0.beta2'),
            ('c7fc3d16ed9dc0b19f0d27583ca661a64562d21e', '2.1.0.rc1'),
            ('edc0a2d02a0cc8eae8b67a3a275f65cd126c05b1', '2.1.0.rc2'),
        ]

        given_ids = [(x.identifier, x.verbose_name) for x in
                     self.project.vcs_repo().parse_tags(data)]
        assert expected_tags == given_ids


class TestHgBackend(RTDTestCase):
    fixtures = ['eric.json']

    def setUp(self):
        hg_repo = make_test_hg()
        super(TestHgBackend, self).setUp()
        self.eric = User.objects.get(username='eric')
        self.project = Project.objects.create(
            name="Test Project",
            repo_type="hg",
            #Our top-level checkout
            repo=hg_repo
        )
        self.project.users.add(self.eric)

    def test_parse_branches(self):
        data = """\
        stable
        default
        """

        expected_ids = ['stable', 'default']
        given_ids = [x.identifier for x in
                     self.project.vcs_repo().parse_branches(data)]
        assert expected_ids == given_ids

    def test_checkout(self):
        repo = self.project.vcs_repo()
        repo.checkout()
        assert exists(repo.working_dir)

    def test_parse_tags(self):
        data = """\
        tip                            13575:8e94a1b4e9a4
        1.8.1                          13573:aa1f3be38ab1
        1.8                            13515:2616325766e3
        1.7.5                          13334:2b2155623ee2
         """
        expected_tags = [
            ('aa1f3be38ab1', '1.8.1'),
            ('2616325766e3', '1.8'),
            ('2b2155623ee2', '1.7.5'),
        ]

        given_ids = [(x.identifier, x.verbose_name) for x in
                     self.project.vcs_repo().parse_tags(data)]
        assert expected_tags == given_ids
