from django.conf import settings
from github2.client import Github
from vcs_support.base import BaseContributionBackend
import base64
import os
import urllib
import urllib2


GITHUB_URLS = ('git://github.com', 'https://github.com', 'http://github.com')
GITHUB_TOKEN = getattr(settings, 'GITHUB_TOKEN', None)
GITHUB_USERNAME = getattr(settings, 'GITHUB_USERNAME', None)
GITHUB_OKAY = GITHUB_TOKEN and GITHUB_USERNAME


class GithubContributionBackend(BaseContributionBackend):
    def __init__(self, *args, **kwargs):
        super(GithubContributionBackend, self).__init__(*args, **kwargs)
        self.gh = Github(username=GITHUB_USERNAME, api_token=GITHUB_TOKEN)
        
    def _run_command(self, *args):
        print args
        ret = super(GithubContributionBackend, self)._run_command(*args)
        print ret
        return ret
        
    @classmethod
    def accepts(cls, url):
        return url.startswith(GITHUB_URLS) and GITHUB_OKAY
    
    def _get_branch_identifier(self, branch):
        identifier = 'rtd-%s-%s' % (branch.user.username, branch.pk)
        if self._branch_exists(identifier):
            return identifier
        self._create_branch(identifier)
        return identifier
    
    def _branch_exists(self, identifier):
        return identifier in self._run_command('git', 'branch')[1]
    
    def _create_branch(self, identifier):
        self.repo.update()
        self._run_command('git', 'branch', '--track', identifier, 'master')
    
    def get_branch_file(self, branch, filename):
        """
        git show branch:file
        """
        identifier = self._get_branch_identifier(branch)
        return self._run_command('git', 'show', '%s:%s' % (identifier, filename))[1]
    
    def set_branch_file(self, branch, filename, contents, comment=''):
        """
        git checkout branch
        git commit --author "Name Surname <email@address.com>" -m comment
        git checkout master
        """
        identifier = self._get_branch_identifier(branch)
        self._run_command('git', 'checkout', identifier)
        with self._open_file(filename, 'wb') as fobj:
            fobj.write(contents)
        self._run_command('git', 'add', filename)
        if not comment:
            comment = 'no comment'
        if branch.user.first_name and branch.user.last_name:
            name = '%s %s' % (branch.user.first_name, branch.user.last_name)
        else:
            name = branch.user.username
        email = branch.user.email
        author = '%s <%s>' % (name, email)
        self._run_command('git', 'commit', '-m', comment, '--author', author)
        self._run_command('git', 'checkout', 'master')
    
    def push_branch(self, branch, title='', comment=''):
        """
        Pushes a branch upstream.
        
        Since the python github API libraries don't support pull requests, we'll
        have to do it manually using urllib2 :(
        """
        identifier = self._get_branch_identifier(branch)
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
        self._run_command('git', 'branch', '-D', identifier)
        
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
        return '%s/%s' % (self._gh_user(), self._gh_reponame())

    def _gh_user(self):
        return self.repo_url.split('/')[-2]
    
    def _gh_reponame(self):
        name = self.repo_url.split('/')[-1]
        if name.endswith('.git'):
            return name[:-4]
        return name
        
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
        self._run_command('git', 'push', 'rtd', identifier)
        
    def _has_fork(self):
        return self._gh_reponame() in [r.name for r in self.gh.repos.list(GITHUB_USERNAME)]
    
    def _fork(self):
        print 'forking %s to %s' % (self._gh_name(), GITHUB_USERNAME)
        print self.gh.repos.fork(self._gh_name())
        
    def get_env(self):
        env = super(GithubContributionBackend, self).get_env()
        env['GIT_DIR'] = os.path.join(self.working_dir, '.git')
        return env