"""This module implements the optional wandb integration for the subnet module"""

from os import environ
from dotenv import load_dotenv
from bittensor import logging
import time

class WandbRuleFromResponse:
    @staticmethod
    def log_from_object_rules(suffix, response):
        uid = response.get("UID")
        hotkey = response.get("hotkey")
        return {
            "engine_confidence": {f"{uid}:{hotkey}_{response.get('name', '_')}": response.get("confidence", {})},
            "confidence": {f"{uid}:{hotkey}_{suffix}": response.get("response", {}).get("confidence")},
            "score_total": {f"{uid}:{hotkey}_{suffix}": response.get("scored_response", {}).get("scores", {}).get("total")},
            "score_distance": {f"{uid}:{hotkey}_{suffix}": response.get("scored_response", {}).get("scores", {}).get("distance")},
            "score_speed": {f"{uid}:{hotkey}_{suffix}": response.get("scored_response", {}).get("scores", {}).get("speed")},
            "raw_score_distance": {f"{uid}:{hotkey}_{suffix}": response.get("scored_response", {}).get("raw_scores", {}).get("distance")},
            "raw_score_speed": {f"{uid}:{hotkey}_{suffix}": response.get("scored_response", {}).get("raw_scores", {}).get("speed")},
            "weight_score_new": {f"{uid}:{hotkey}_{suffix}": response.get("weight_scores", {}).get("new")},
            "weight_score_old": {f"{uid}:{hotkey}_{suffix}": response.get("weight_scores", {}).get("old")},
            "weight_score_change": {f"{uid}:{hotkey}_{suffix}": response.get("weight_scores", {}).get("change")},
        }.get(suffix)


class WandbHandler(WandbRuleFromResponse):

    def __init__(self):
        # Get the required variables in order to initialize the wandb connection
        load_dotenv()
        key = environ.get("WANDB_KEY")
        project = environ.get("WANDB_PROJECT")
        entity = environ.get("WANDB_ENTITY")
        self.use_wandb = False
        self._wandb_logs = []
        # Validate the environmental variables are present
        if all([key, project, entity]):
            # Initialize
            try:
                import wandb
                wandb.login(key=key, verify=True)
                self.wandb_run = wandb.init(project=project, entity=entity)
                self.use_wandb = True
            except Exception as e:
                logging.error(f"Unable to init wandb connectivity: {e}")
                raise RuntimeError(f"Unable to init wandb connectivity: {e}") from e

        # Define class variables
        self.log_timestamp = None

    @property
    def wandb_logs(self):
        return self._wandb_logs

    @wandb_logs.setter
    def set_wandb_logs(self, value):
        self._wandb_logs = value

    @wandb_logs.setter
    def append_wandb_logs(self, value):
        self._wandb_logs.extend(value)

    def set_timestamp(self):
        """Sets the timestamp to be used as the step"""
        self.log_timestamp = int(time.time())

    def discharge_logs(self):
        logs = iter(self.wandb_logs)
        while next(logs, None):
            self.log(next(logs))
        self.wandb_logs.clear()

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