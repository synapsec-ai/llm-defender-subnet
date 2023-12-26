from argparse import ArgumentParser
import logging
from time import sleep
import git
import subprocess


logging.basicConfig(level=logging.INFO)

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
                logging.info('Changes detected in remote branch: %s', args.branch)
                logging.info('Pulling remote branch: %s', args.branch)
                origin.pull(args.branch)
                repo.git.checkout(args.branch)
                logging.info('Checked out to branch: %s', args.branch)

                # Restart pm2 instances
                for instance_name in args.pm2_instance_names:
                    try:
                        subprocess.run(f'pm2 restart {instance_name}', check=True, shell=True)
                        logging.info('Restarted PM2 process: %s', instance_name)
                        logging.info('Sleeping for 30 seconds.')
                        sleep(30)
                    except subprocess.CalledProcessError as e:
                        logging.error('Unable to restart PM2 instance: %s', e)
                
                logging.info('All processes have been restarted')
            else:
                logging.info('No changes detected in remote branch: %s', args.branch)

            logging.info('Sleeping for %s seconds.', args.interval)
            sleep(int(args.interval))
        except Exception as e:
            logging.error('Error occurred: %s', e)
            raise Exception from e

if __name__ == '__main__':
    parser = ArgumentParser()

    parser.add_argument("--pm2_instance_names", nargs='+', help="List of PM instances to keep up-to-date")
    parser.add_argument("--branch", action="store", help="Git branch to monitor")
    parser.add_argument("--repo", action="store", help="Git repository address")
    parser.add_argument("--interval", action="store", help="Interval to check for any new updates")

    args = parser.parse_args()
    run(args)