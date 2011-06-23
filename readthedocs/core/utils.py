import getpass
import os

from django.conf import settings


def copy_to_app_servers(full_build_path, target, mkdir=True):
    """
    A helper to copy a directory across app servers
    """
    print "Copying %s to %s" % (full_build_path, target)
    for server in settings.MULTIPLE_APP_SERVERS:
        os.system("ssh %s@%s mkdir -p %s" % (getpass.getuser(), server, target))
        ret = os.system("rsync -e 'ssh -T' -av --delete %s/ %s@%s:%s" %
                        (full_build_path, getpass.getuser(), server, target))
        if ret != 0:
            print "COPY ERROR to app servers."


def copy_file_to_app_servers(from_file, to_file):
    """
    A helper to copy a single file across app servers
    """
    print "Copying %s to %s" % (from_file, to_file)
    to_path = '/'.join(to_file.split('/')[0:-1])
    for server in settings.MULTIPLE_APP_SERVERS:
        os.system("ssh %s@%s mkdir -p %s" % (getpass.getuser(), server, to_path))
        ret = os.system("rsync -e 'ssh -T' -av --delete %s %s@%s:%s" % (from_file, getpass.getuser(), server, to_file))
        if ret != 0:
            print "COPY ERROR to app servers."
