"""Module for llm-defender-subnet neurons.

Neurons are the backbone of the subnet and are providing the subnet
users tools to interact with the subnet and participate in the
value-creation chain. There are two primary neuron classes: validator and miner.

Typical example usage:

    miner = MinerNeuron(profile="miner")
    miner.run()
"""
from argparse import ArgumentParser
from os import path, makedirs, rename
from datetime import datetime
import bittensor as bt
from llm_defender.base.utils import sign_data
import requests
import secrets
import pickle
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
        self.path_hotkey = None
        self.profile = profile
        self.step = 0
        self.last_updated_block = 0
        self.base_path = f"{path.expanduser('~')}/.llm-defender-subnet"
        self.subnet_version = subnet_version
        self.used_nonces = []

        # Load used nonces if they exists
        self.load_used_nonces()

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
        self.path_hotkey = config.wallet.hotkey
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

    def remote_logger(self, hotkey, message: dict) -> bool:
        """This function is responsible for sending validation metrics
        and miner response data to centralized log repository.
        
        The data is used to construct a dashboard to measure the
        performance of the subnet. It is important for all validators to
        send out the metrics towards the centralized logger.

        You may opt-out from the data collection by setting the
        --disable_remote_logging argument in the validator pm2 file.
        """

        nonce = str(secrets.token_hex(24))
        timestamp = str(int(time.time()))

        signature = sign_data(hotkey=hotkey, data=f'{nonce}-{timestamp}')

        headers = {
            "X-Hotkey": hotkey.ss58_address,
            "X-Signature": signature,
            "X-Nonce": nonce,
            "X-Timestamp": timestamp,
            "X-API-Key":hotkey.ss58_address
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
    
    def save_used_nonces(self):
        """Saves used nonces to a local file"""

        if len(self.used_nonces) > 1000000:
            self.used_nonces = self.used_nonces[-500000:]
            bt.logging.info("Truncated list of used_nonces")
        with open(f"{self.base_path}/{self.path_hotkey}_{self.profile}_used_nonces.pickle", "wb") as pickle_file:
            pickle.dump(self.used_nonces, pickle_file)

        bt.logging.info("Saved used nonces to a file")
    
    def load_used_nonces(self):
        """Loads used nonces from a file"""
        state_path = f"{self.base_path}/{self.path_hotkey}_{self.profile}_used_nonces.pickle"
        if path.exists(state_path):
            try:
                with open(state_path, "rb") as pickle_file:
                    self.used_nonces = pickle.load(pickle_file)

                bt.logging.info("Loaded used nonces from a file")
            except Exception as e:
                bt.logging.error(
                    f"Used nonces reset because a failure to read the used nonces data, error: {e}"
                )

                # Rename the used nonces file if exception
                # occurs and reset the default state
                rename(
                    state_path,
                    f"{state_path}-{int(datetime.now().timestamp())}.autorecovery",
                )
                self.used_nonces = []

    def validate_nonce(self, nonce):
        """This function validates that the nonce has not been seen
        before."""
        if nonce not in self.used_nonces:
            self.used_nonces.append(nonce)
            return True
        return False