


def git_pull():
    "Updates the repository"
    run("cd $(working_dir)/$(repo)/; git pull $(parent) $(branch)")

def git_reset():
    "Resets the repository to the specified version."
    run("cd $(working_dir)$(repo)/; git reset --hard $(hash)")

def production():
    config.fab_hosts = ['tracks.stowers']
    config.repos = (('tracks','origin','master),)

def reboot():
    "Reboot nginx server"
    sudo("sudo /sbin/service nginx restart")

def pull(require('fab_hosts'), provided_by=[production])
    for repo, parent, branch in config.repos:
        config.repo = repo
        config.parent = parent
        config.branch = branch
        invoke(git_pull)

def git_reset(repo, hash_id):
    """Reset all git repositories to specified hash id
       Usage: fab reset:repo=tracks, hash=hash_id
    """
    require("fab_hosts", provided_by=[production])
    config.hash = hash_id
    config.repo = repo
    invoke(git_reset)


# skipping setup function, due to existing database.
def setup():
    raise NotImplementedError('generic server setup is NOT IMPLEMENTED')