from __future__ import with_statement
from fabric.api import abort, local, settings, env, run, cd, task, execute, runs_once, prefix
from fabric.contrib.console import confirm
from fabric.network import disconnect_all

"""
IMPORTANT: Deployment assumes all feature branches ready for production have been committed and merged into master
           and that the user is currently on master to indicate readiness.
"""


env.hosts = [
    'ssh.pythonanywhere.com',
]

# Set the username
env.user   = "amberdiehl"


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


def remote_pull():
    """
    Pull changes for deployment
    :return:
    """
    with cd("~/dandeliondiary_project/dandeliondiary"):
        run("git pull origin")
    # credentials must be supplied manually


@task
def remote_get_migration_status():
    with settings(warn_only=True):
        return run("./manage.py showmigrations --list --settings=dandeliondiary.settings.production "
                   "| grep '\[ ]'")


@task
@runs_once
def remote_run_migrations():
    """
    Determine if there are migrations to run and, if so, run them
    :return:
    """
    with cd("~/dandeliondiary_project/dandeliondiary"):
        with prefix('workon dd-venv'):
            result = execute(remote_get_migration_status)
            if result['ssh.pythonanywhere.com'] == '':
                print_message("No migrations found.")
            else:
                print_message("Applying migrations...")
                print(result['ssh.pythonanywhere.com'])
                run("./manage.py migrate --settings=dandeliondiary.settings.production")


@task
def remote_restart_server():
    """
    Restart the web server
    :return:
    """
    print_message('Restarting the web server...')
    run("touch /var/www/www_dandeliondiary_com_wsgi.py")


def exit_remote():
    """
    Exit from ssh session
    :return:
    """
    disconnect_all()


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

    remote_pull()

    remote_run_migrations()

    remote_restart_server()

    exit_remote()
