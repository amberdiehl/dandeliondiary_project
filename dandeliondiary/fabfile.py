from fabric.api import local, abort
from fabric.contrib.console import confirm

"""
IMPORTANT: Deployment assumes all feature branches ready for production have been committed and merged into master
"""


def print_message(msg):

    print(' ')
    print('==> ' + msg + '...')
    print(' ')


def check_local_branch():

    print_message("Checking local branch")
    my_branch = local('git rev-parse --abbrev-ref HEAD', capture=True)
    print("Current branch is: %s" % my_branch)
    if my_branch != 'master':
        abort('Please ensure all changes ready for release are committed to master and make master current branch.')


def run_tests():
    """
    Make sure tests pass before continuing
    :return:
    """
    local("./manage.py test capture compare --settings=dandeliondiary.settings.local_test")


def push():
    """
    Push master to remote (GitHub)
    :return:
    """
    if not confirm("At push to master; continue?"):
        abort("Aborted deploy at your request.")

    local("git push origin")


def deploy():
    """
    Deployment assumes that all feature branches ready for deployment have already been merged to master
    :return:
    """

    run_tests()

    check_local_branch()

    push()
