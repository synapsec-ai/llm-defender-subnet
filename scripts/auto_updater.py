from argparse import ArgumentParser
import logging
import sys
from time import sleep
import git
import subprocess
import random


logger = logging.getLogger('logger')
logger.setLevel(logging.INFO)
logHandler = logging.StreamHandler(sys.stdout)
logHandler.setLevel(logging.INFO)
logger.addHandler(logHandler)

def run(args):
    """Monitors the given git branch for updates and restart given PM2
    instances if updates are found"""

    while(True):
        try:
            # Setup git repository objects
            repo = git.Repo()
            origin = repo.remotes.origin

            # Fetch updates from the remote registry
            origin.fetch()

            # Check if there are changes in the remote repository
            if repo.refs[args.branch].commit != repo.refs[f'origin/{args.branch}'].commit:
                logger.info('Changes detected in remote branch: %s', args.branch)
                logger.info('Pulling remote branch: %s', args.branch)
                origin.pull(args.branch)
                repo.git.checkout(args.branch)
                logger.info('Checked out to branch: %s', args.branch)

                # Restart pm2 instances
                for instance_name in args.pm2_instance_names:
                    try:
                        sleep_duration = random.randint(15,90)
                        logger.info('Sleeping for %s seconds before restart', sleep_duration)
                        sleep(sleep_duration)
                        subprocess.run(f'git checkout {args.branch} && pm2 restart {instance_name}', check=True, shell=True)
                        logger.info('Restarted PM2 process: %s', instance_name)
                    except subprocess.CalledProcessError as e:
                        logger.error('Unable to restart PM2 instance: %s', e)
                
                logger.info('All processes have been restarted')
            else:
                logger.info('No changes detected in remote branch: %s', args.branch)

            logger.info('Sleeping for %s seconds.', args.update_interval)
            sleep(int(args.update_interval))
        except Exception as e:
            logger.error('Error occurred: %s', e)
            raise Exception from e

if __name__ == '__main__':
    parser = ArgumentParser()

    parser.add_argument("--pm2_instance_names", nargs='+', help="List of PM instances to keep up-to-date")
    parser.add_argument("--branch", action="store", help="Git branch to monitor")
    parser.add_argument("--repo", action="store", help="Git repository address")
    parser.add_argument("--update_interval", action="store", help="Interval to check for any new updates")

    args = parser.parse_args()
    run(args)