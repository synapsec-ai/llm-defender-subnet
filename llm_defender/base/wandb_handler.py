"""This module implements the optional wandb integration for the subnet module"""

from os import environ
from dotenv import load_dotenv
from bittensor import logging
import wandb
import time


class WandbHandler:

    def __init__(self):
        # Get the required variables in order to initialize the wandb connection
        load_dotenv()
        key = environ.get("WANDB_KEY")
        project = environ.get("WANDB_PROJECT")
        entity = environ.get("WANDB_ENTITY")

        # Validate the environmental variables are present
        if key is None:
            raise ValueError("WANDB_KEY is not set")
        if project is None:
            raise ValueError("WANDB_PROJECT is not set")
        if entity is None:
            raise ValueError("WANDB_ENTITY is not set")

        # Initialize
        try:
            wandb.login(key=key, verify=True)
            self.wandb_run = wandb.init(project=project, entity=entity)
        except Exception as e:
            logging.error(f"Unable to init wandb connectivity: {e}")
            raise RuntimeError(f"Unable to init wandb connectivity: {e}") from e

        # Define class variables
        self.log_timestamp = None

    def set_timestamp(self):
        """Sets the timestamp to be used as the step"""
        self.log_timestamp = int(time.time())

    def log(self, data):
        """Logs data to wandb
        
        Arguments:
            data:
                Data object to be logged into the wandb
        """
        try:
            self.wandb_run.log(data, self.log_timestamp)
        except Exception as e:
            logging.error(f'Unable to log into wandb: {e}')
    
    def custom_wandb_metric(self, data, **kwargs):
        """
        Allows for custom wandb logging of metrics (in engines, etc.).

        Arguments:
            data:
                This must be a dict instance, where the key will be the 
                title of the graph in wandb, and the associated value will
                be the y-axis value of the graph.
            **kwargs:
                Applies to wandb.log()
            step:
                If specified, this will be the x-axis of the graph.

        Returns:
            None
        """
        self.wandb_run.wandb.log(data,**kwargs)