from django.conf import settings
from github2.client import Github
from projects.exceptions import ProjectImportError
from vcs_support.base import BaseVCS, VCSTag, BaseContributionBackend
import base64
import os
import urllib
import urllib2

GITHUB_URLS = ('git://github.com', 'https://github.com')
GITHUB_TOKEN = getattr(settings, 'GITHUB_TOKEN', None)
GITHUB_USERNAME = getattr(settings, 'GITHUB_USERNAME', None)
GITHUB_OKAY = GITHUB_TOKEN and GITHUB_USERNAME


class BaseGIT(object):
    def get_env(self):
        env = super(Backend, self).get_env()
        env['GIT_DIR'] = os.path.join(self.working_dir, '.git')
        return env


class GithubContributionBackend(BaseContributionBackend, BaseGIT):
    def __init__(self, *args, **kwargs):
        super(GithubContributionBackend, self).__init__(*args, **kwargs)
        self.gh = Github(username=GITHUB_USERNAME, api_token=GITHUB_TOKEN)
        
    @classmethod
    def accepts(cls, url):
        return url.startswith(GITHUB_URLS) and GITHUB_OKAY
    
    def _get_branch_identifier(self, user):
        identifier = 'rtd-%s' % user.username
        if self._branch_exists(identifier):
            return identifier
        self._create_branch(identifier)
        return identifier
    
    def _branch_exists(self, identifier):
        return identifier in self._run_command('git', 'branch')[1]
    
    def _create_branch(self, identifier):
        self._run_command('git', 'branch', '--track', identifier, 'master')
    
    def get_branch_file(self, user, filename):
        """
        git show branch:file
        """
        identifier = self._get_branch_identifier(user)
        return self._run_command('git', 'show', '%s:%s' % (identifier, filename))[1]
    
    def set_branch_file(self, user, filename, contents, comment=''):
        """
        git checkout branch
        git commit --author "Name Surname <email@address.com>" -m comment
        git checkout master
        """
        identifier = self._get_branch_identifier(user)
        self._run_command('git', 'checkout', identifier)
        with self._open_file(filename, 'wb') as fobj:
            fobj.write(contents)
        self._run_command('git', 'add', filename)
        if not comment:
            comment = 'no comment'
        if user.first_name and user.last_name:
            name = '%s %s' % (user.first_name, user.last_name)
        else:
            name = user.username
        email = user.email
        author = '%s <%s>' % (name, email)
        self._run_command('git', 'commit', '-m', comment, '--author', author)
        self._run_command('git', 'checkout', 'master')
    
    def push_branch(self, user, title='', comment=''):
        """
        Pushes a branch upstream.
        
        Since the python github API libraries don't support pull requests, we'll
        have to do it manually using urllib2 :(
        """
        identifier = self._get_branch_identifier(user)
        print 'pushing branch %s in %s' % (identifier, self._gh_name())
        # first push the branch to the rtd-account on github.
        self._check_remote()
        self._push_remote(identifier)
        # now make the pull request.
        if not title:
            title = 'Documentation changes from readthedocs.org'
        if not comment:
            comment = 'These changes have been done on readthedocs.org'
        self._pull_request(identifier, title, comment)
        
    def _pull_request(self, identifier, title, comment):
        """
        Open an actual pull request
        """
        print 'pull request %s:%s to %s (%s/%s)' % (GITHUB_USERNAME, identifier, self._gh_name(), title, comment)
        url = 'https://github.com/api/v2/json/pulls/%s' % self._gh_name()
        print url
        request = urllib2.Request(url)
        auth = base64.encodestring('%s/token:%s' % (GITHUB_USERNAME, GITHUB_TOKEN))[:-1]
        request.add_header("Authorization", 'Basic %s' % auth)
        data = {
            'base': 'master',
            'head': '%s:%s' % (GITHUB_USERNAME, identifier),
            'title': title,
            'body': comment,
        }
        pull_request_data = [("pull[%s]" % k, v) for k, v in data.items()]
        postdata = urllib.urlencode(pull_request_data)
        print 'postdata:'
        print postdata
        handler = urllib2.urlopen(request, postdata)
        print handler.headers.dict
        print handler.read()
    
    def _gh_name(self):
        user, repo = self.repo_url.split('/')[-2:]
        return '%s/%s' % (user, repo[:-4])
    
    def _gh_reponame(self):
        return self.repo_url.split('/')[-1][:-4]
        
    def _check_remote(self):
        """
        Check if the RTD remote is available in this repository, if not, add it.
        """
        print 'checking remote'
        if not self._has_fork():
            print 'no fork available'
            self._fork()
        else:
            print 'fork found'
        if 'rtd' not in self._run_command('git', 'remote')[1]:
            print 'rtd remote not yet specified'
            self._run_command('git', 'remote', 'add', 'rtd', self._get_remote_name())
        else:
            print 'rtd remote found'
            
    def _get_remote_name(self):
        return 'git@github.com:%s/%s.git' % (GITHUB_USERNAME, self._gh_reponame())
    
    def _push_remote(self, identifier):
        """
        push a local branch to the RTD remote
        """
        print 'pushing %s to remote %s' % (identifier, self._get_remote_name())
        print self._run_command('git', 'push', 'rtd', identifier)
        
    def _has_fork(self):
        return self._gh_reponame() in [r.name for r in self.gh.repos.list(GITHUB_USERNAME)]
    
    def _fork(self):
        print 'forking %s to %s' % (self._gh_name(), GITHUB_USERNAME)
        print self.gh.repos.fork(self._gh_name())
        

class Backend(BaseVCS, BaseGIT):
    supports_tags = True
    contribution_backends = [GithubContributionBackend]
    
    def update(self):
        retcode = self._run_command('git', 'status')[0]
        if retcode == 0:
            self._pull()
        else:
            self._clone()
            
    def _pull(self):
        retcode = self._run_command('git', 'fetch')[0]
        if retcode != 0:
            raise ProjectImportError(
                "Failed to get code from '%s' (git fetch): %s" % (self.repo_url, retcode)
            )
        retcode = self._run_command('git', 'reset', '--hard', 'origin/master')[0]
        if retcode != 0:
            raise ProjectImportError(
                "Failed to get code from '%s' (git reset): %s" % (self.repo_url, retcode)
            )
        
    def _clone(self):
        retcode = self._run_command('git', 'clone', '--quiet', self.repo_url, '.')[0]
        if retcode != 0:
            raise ProjectImportError(
                "Failed to get code from '%s' (git clone): %s" % (self.repo_url, retcode)
            )
    
    def get_tags(self):
        retcode, stdout = self._run_command('git', 'show-ref', '--tags')[:2]
        # error (or no tags found)
        if retcode != 0:
            return []
        return self._parse_tags(stdout)
    
    def _parse_tags(self, data):
        """
        Parses output of show-ref --tags, eg:
        
            3b32886c8d3cb815df3793b3937b2e91d0fb00f1 refs/tags/2.0.0
            bd533a768ff661991a689d3758fcfe72f455435d refs/tags/2.0.1
            c0288a17899b2c6818f74e3a90b77e2a1779f96a refs/tags/2.0.2
            a63a2de628a3ce89034b7d1a5ca5e8159534eef0 refs/tags/2.1.0.beta2
            c7fc3d16ed9dc0b19f0d27583ca661a64562d21e refs/tags/2.1.0.rc1
            edc0a2d02a0cc8eae8b67a3a275f65cd126c05b1 refs/tags/2.1.0.rc2
        
        Into VCSTag objects with the tag name as verbose_name and the commit
        hash as identifier.
        """
        # parse the lines into a list of tuples (commit-hash, tag ref name)
        raw_tags = [line.split(' ', 1) for line in data.strip('\n').split('\n')]
        vcs_tags = []
        for commit_hash, name in raw_tags:
            clean_name = self._get_clean_tag_name(name)
            vcs_tags.append(VCSTag(self, commit_hash, clean_name))
        return vcs_tags
    
    def _get_clean_tag_name(self, name):
        return name.split('/', 2)[2]
    
    def checkout(self, identifier=None):
        if not identifier:
            identifier = 'master'
        self._run_command('git', 'reset', '--hard', identifier)