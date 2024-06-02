"""This module is responsble for managing the configuration parameters
used by the llm_defender module"""

from os import environ
from dotenv import load_dotenv

load_dotenv()


class ModuleConfig:
    """This class is used to standardize the presentation of
    configuration parameters used throughout the llm_defender module"""

    def __init__(self):

        # Determine module code version
        self.__version__ = "0.8.0"

        # Convert the version into a single integer
        self.__version_split__ = self.__version__.split(".")
        self.__spec_version__ = (
            (1000 * int(self.__version_split__[0]))
            + (10 * int(self.__version_split__[1]))
            + (1 * int(self.__version_split__[2]))
        )

        # Initialize with default values
        self.__config__ = {
            "wandb_enabled": False,
            "module_version": self.__spec_version__,
        }

    def _read_environmental_variables(self) -> None:
        """This module reads configuration parameters from environmental
        variables and adjusts the default list accordingly."""

        # Get wandb status
        wandb_enabled = environ.get("WANDB_ENABLE")
        if wandb_enabled is not None and int(wandb_enabled) == 1:
            self.set_config(key="wandb_enabled", value=True)

    def get_full_config(self) -> dict:
        """Returns the full configuration data"""
        return self.__config__

    def set_config(self, key, value) -> dict:
        """Updates the configuration value of a particular key and
        returns updated configuration"""

        if key and value:
            self.__config__[key] = value
        elif key and isinstance(value, bool):
            self.__config__[key] = value
        else:
            raise ValueError(f"Unable to set the value: {value} for key: {key}")
        return self.get_full_config()
    
    def get_config(self, key):
        """Returns the configuration for a particular key"""

        value = (self.get_full_config())[key]

        if not value and not isinstance(value, bool):
            raise ValueError(f"Unable to get the value: {value} for key: {key}")

        return value
