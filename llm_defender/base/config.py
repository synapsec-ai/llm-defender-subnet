"""This module is responsble for managing the configuration parameters
used by the llm_defender module"""

import yaml
import importlib.resources as pkg_resources
import llm_defender as LLMDefender


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

    def load_default_config(self):
        with pkg_resources.open_text(LLMDefender, "defaults.yaml") as f:
            return yaml.safe_load(f)

    def _recursive_merge(self, default, user):
        for key, value in user.items():
            if isinstance(value, dict) and key in default:
                default[key] = self._recursive_merge(default[key], value)
            else:
                default[key] = value
        return default

    def load_config(self, user_config_path=None):
        config = self.load_default_config()
        if user_config_path:
            with open(user_config_path, "r", encoding="utf-8") as f:
                user_config = yaml.safe_load(f)
                config = self._recursive_merge(config, user_config)
        return config

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
