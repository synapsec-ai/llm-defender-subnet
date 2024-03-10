"""Module for llm-defender-subnet neurons.

Neurons are the backbone of the subnet and are providing the subnet
users tools to interact with the subnet and participate in the
value-creation chain. There are two primary neuron classes: validator and miner.

Typical example usage:

    miner = MinerNeuron(profile="miner")
    miner.run()
"""
from argparse import ArgumentParser
from os import path, makedirs
import bittensor as bt
from llm_defender.base.utils import sign_data
import requests
import secrets
import time
import json
from llm_defender import __spec_version__ as subnet_version


class BaseNeuron:
    """Summary of the class

    Class description

    Attributes:
        parser:
            Instance of ArgumentParser with the arguments given as
            command-line arguments in the execution script
        profile:
            Instance of str depicting the profile for the neuron
    """

    def __init__(self, parser: ArgumentParser, profile: str) -> None:
        self.parser = parser
        self.profile = profile
        self.step = 0
        self.last_updated_block = 0
        self.base_path = f"{path.expanduser('~')}/.llm-defender-subnet"
        self.subnet_version = subnet_version

    def config(self, bt_classes: list) -> bt.config:
        """Applies neuron configuration.

        This function attaches the configuration parameters to the
        necessary bittensor classes and initializes the logging for the
        neuron.

        Args:
            bt_classes:
                A list of Bittensor classes the apply the configuration
                to

        Returns:
            config:
                An instance of Bittensor config class containing the
                neuron configuration

        Raises:
            AttributeError:
                An error occurred during the configuration process
            OSError:
                Unable to create a log path.

        """
        try:
            for bt_class in bt_classes:
                bt_class.add_args(self.parser)
        except AttributeError as e:
            bt.logging.error(
                f"Unable to attach ArgumentParsers to Bittensor classes: {e}"
            )
            raise AttributeError from e

        config = bt.config(self.parser)

        # Construct log path
        log_path = f"{self.base_path}/logs/{config.wallet.name}/{config.wallet.hotkey}/{config.netuid}/{self.profile}"

        # Create the log path if it does not exists
        try:
            config.full_path = path.expanduser(log_path)
            if not path.exists(config.full_path):
                makedirs(config.full_path, exist_ok=True)
        except OSError as e:
            bt.logging.error(f"Unable to create log path: {e}")
            raise OSError from e

        return config

    def remote_logger(self, wallet, message: dict) -> bool:
        nonce = str(secrets.token_hex(24))
        timestamp = str(int(time.time()))

        headers = {
            "X-Hotkey": wallet.hotkey.ss58_address,
            "X-Signature": sign_data(wallet=wallet, data=f'{nonce}-{timestamp}'),
            "X-Nonce": nonce,
            "X-Timestamp": timestamp,
        }

        data = message

        res = self.requests_post(url="https://logger.synapsec.ai/logger", headers=headers, data=data)

        if res:
            return True
        return False
  
    def requests_post(self, url, headers: dict, data: dict, timeout: int = 12) -> dict:
        
        try:
            # get prompt
            res = requests.post(url=url, headers=headers, data=json.dumps(data), timeout=timeout)
            # check for correct status code
            if res.status_code == 200:
                return res.json()
            
            bt.logging.warning(f"Unable to connect to remote host: {url}: HTTP/{res.status_code} - {res.json()}")
            return {}
        except requests.exceptions.ReadTimeout as e:
            bt.logging.error(f"Remote API request timed out: {e}")
        except requests.exceptions.JSONDecodeError as e:
            bt.logging.error(f"Unable to read the response from the remote API: {e}")
        except requests.exceptions.ConnectionError as e:
            bt.logging.error(f"Unable to connect to the remote API: {e}")
        except Exception as e:
            bt.logging.error(f'Generic error during request: {e}')
