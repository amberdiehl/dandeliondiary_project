from __future__ import with_statement
from fabric.api import abort, local, settings
from fabric.contrib.console import confirm

"""
IMPORTANT: Deployment assumes all feature branches ready for production have been committed and merged into master
           and that the user is currently on master to indicate readiness.
"""


def print_message(msg):

    print(' ')
    print('==> ' + msg)
    print(' ')


def check_local_branch():
    """
    Validate user is on master branch
    :return:
    """
    print_message("Validating current branch:")
    my_branch = local('git rev-parse --abbrev-ref HEAD', capture=True)
    print("Current branch is: %s" % my_branch)
    if my_branch != 'master':
        abort('Please ensure all changes ready for release are committed and merged with master and make master '
              'working branch.')


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


def ssh():
    """
    Login into PythonAnywhere host
    :return:
    """
    local("ssh amberdiehl@ssh.pythonanywhere.com")
    # password must be supplied manually


def pull():
    """
    Pull changes for deployment
    :return:
    """
    local("git pull origin")
    # credentials must be supplied manually


def run_migrations():
    """
    Determine if there are migrations to run and, if so, run them
    :return:
    """
    with settings(warn_only=True):
        migrations = local("./manage.py showmigrations --list --settings=dandeliondiary.settings.production "
                           "| grep '\[ ]'", capture=True)
    if migrations.failed:
        print_message("No migrations found.")
    else:
        print_message("Applying migrations...")
        local("./manage.py migrate --settings=dandeliondiary.settings.production")


def restart_server():
    """
    Restart the server
    :return:
    """
    local("touch /var/www/www_dandeliondiary_com_wsgi.py")


def exit_ssh():
    """
    Exit from ssh session
    :return:
    """
    local("exit")


"""
Main scripts
"""


def deploy():
    """
    Deploy latest release/changes for Dandelion Diary to production
    :return:
    """

    check_local_branch()

    run_tests()

    push()

    ssh()

    pull()

    run_migrations()

    restart_server()

    exit_ssh()
