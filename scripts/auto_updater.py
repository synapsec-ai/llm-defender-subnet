from argparse import ArgumentParser
import logging
import sys
from time import sleep
import subprocess
import random
from pathlib import Path


logger = logging.getLogger("logger")
logger.setLevel(logging.INFO)
logHandler = logging.StreamHandler(sys.stdout)
logHandler.setLevel(logging.INFO)
logger.addHandler(logHandler)

def run(args):
    """Monitors the given git branch for updates and restart given PM2
    instances if updates are found"""

    logger.error("As of subnet version v0.9.0 the auto-updater is no longer supported. \
        Using the auto-updater can lead into unforeseen consequences, thus the validators are gracefully shutdown.")

    # Shutdown pm2 instances
    for instance_name in args.pm2_instance_names:
        
        # Only stop non-miners
        if not "miner" in instance_name.lower():
            try:
                sleep_duration = random.randint(15, 90)
                logger.info(
                    "Sleeping for %s seconds before stop", sleep_duration
                )
                sleep(sleep_duration)
                subprocess.run(
                    f"pm2 stop {instance_name}",
                    check=True,
                    shell=True,
                )
                logger.info("Stopped PM2 process: %s", instance_name)

            except subprocess.CalledProcessError as e:
                logger.error("Unable to stop PM2 instance: %s", e)
    
    sys.exit(-1)

if __name__ == "__main__":
    parser = ArgumentParser()

    cwd = Path.cwd()
    repo_name = "llm-defender-subnet"

    if cwd.parts[-1] == repo_name:
        parser.add_argument(
            "--pm2_instance_names",
            nargs="+",
            help="List of PM instances to keep up-to-date",
        )
        parser.add_argument("--branch", action="store", help="Git branch to monitor")
        parser.add_argument(
            "--prepare_miners",
            type=bool,
            action="store",
            default=True,
            help="If you're not running miners or you dont want to prepare them, set this to False",
        )
        parser.add_argument(
            "--update_interval",
            action="store",
            help="Interval to check for any new updates",
        )
        parser.add_argument(
            "--no_validator",
            action="store_true",
            help="This flag must be set if validator is not running on the machine",
        )
        parser.add_argument(
            "--no_miner",
            action="store_true",
            help="This flag must be set if miner is not running on the machine",
        )
        parser.add_argument(
            "--wandb",
            action="store_true",
            help="This flag must be set if wandb is enabled on the machine",
        )

        args = parser.parse_args()
        run(args)
    else:
        logger.error(
            "Invalid current working directory. You must be in the root of the llm-defender-subnet git repository to run this script. Path: %s",
            cwd,
        )
        raise RuntimeError(
            f"Invalid current path: {cwd}. Expecting the path to end with {repo_name}"
        )
