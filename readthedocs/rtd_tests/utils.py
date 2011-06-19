from os import chdir, environ, getcwd
from os.path import abspath, join as pjoin
from shutil import copytree
import subprocess
from tempfile import mkdtemp

def check_output(l, env):
    output = subprocess.Popen(['ls', '-l'], stdout=subprocess.PIPE, env=env).communicate()[0]

def make_test_git():
    directory = mkdtemp()
    path = getcwd()
    sample = abspath(pjoin(path, 'rtd_tests/fixtures/sample_git'))
    directory = pjoin(directory, 'sample_git')
    copytree(sample, directory)
    env = environ.copy()
    env['GIT_DIR'] = pjoin(directory, '.git')
    chdir(directory)
    print check_output(['git', 'init'] + [directory], env=env)
    print check_output(['git', 'add', '.'], env=env)
    print check_output(['git', 'ci', '-m"init"'], env=env)
    chdir(path)
    return directory
