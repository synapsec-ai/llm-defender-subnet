"""Module for prompt-injection neurons for the
llm-defender-subnet.

Long description

Typical example usage:

    foo = bar()
    foo.bar()
"""

import copy
import pickle
import json
from argparse import ArgumentParser
from typing import Tuple
from sys import getsizeof
from datetime import datetime
from os import path, rename
from pathlib import Path
import torch
import secrets
import time
import bittensor as bt
from llm_defender.base.neuron import BaseNeuron
from llm_defender.base.utils import (
    timeout_decorator,
    validate_miner_blacklist,
    validate_numerical_value,
    validate_prompt,
    sign_data,
)
from llm_defender.base import mock_data
from llm_defender.core.validators import penalty
import requests
import llm_defender.core.validators.scoring as scoring

# Load wandb library only if it is enabled
from llm_defender import __wandb__ as wandb

if wandb is True:
    from llm_defender.base.wandb_handler import WandbHandler


class PromptInjectionValidator(BaseNeuron):
    """Summary of the class

    Class description

    Attributes:

    """

    def __init__(self, parser: ArgumentParser):
        super().__init__(parser=parser, profile="validator")

        self.max_engines = 3
        self.timeout = 12
        self.neuron_config = None
        self.wallet = None
        self.subtensor = None
        self.dendrite = None
        self.metagraph = None
        self.scores = None
        self.hotkeys = None
        self.miner_responses = None
        self.max_targets = None
        self.target_group = None
        self.blacklisted_miner_hotkeys = None
        self.load_validator_state = None
        self.prompt = None

        # Enable wandb if it has been configured
        if wandb is True:
            self.wandb_enabled = True
            self.wandb_handler = WandbHandler()
        else:
            self.wandb_enabled = False

    def apply_config(self, bt_classes) -> bool:
        """This method applies the configuration to specified bittensor classes"""
        try:
            self.neuron_config = self.config(bt_classes=bt_classes)
        except AttributeError as e:
            bt.logging.error(f"Unable to apply validator configuration: {e}")
            raise AttributeError from e
        except OSError as e:
            bt.logging.error(f"Unable to create logging directory: {e}")
            raise OSError from e

        return True

    def validator_validation(self, metagraph, wallet, subtensor) -> bool:
        """This method validates the validator has registered correctly"""
        if wallet.hotkey.ss58_address not in metagraph.hotkeys:
            bt.logging.error(
                f"Your validator: {wallet} is not registered to chain connection: {subtensor}. Run btcli register and try again"
            )
            return False

        return True

    def setup_bittensor_objects(
        self, neuron_config
    ) -> Tuple[bt.wallet, bt.subtensor, bt.dendrite, bt.metagraph]:
        """Setups the bittensor objects"""
        try:
            wallet = bt.wallet(config=neuron_config)
            subtensor = bt.subtensor(config=neuron_config)
            dendrite = bt.dendrite(wallet=wallet)
            metagraph = subtensor.metagraph(neuron_config.netuid)
        except AttributeError as e:
            bt.logging.error(f"Unable to setup bittensor objects: {e}")
            raise AttributeError from e

        self.hotkeys = copy.deepcopy(metagraph.hotkeys)

        return wallet, subtensor, dendrite, metagraph

    def initialize_neuron(self) -> bool:
        """This function initializes the neuron.

        The setup function initializes the neuron by registering the
        configuration.

        Args:
            None

        Returns:
            Bool:
                A boolean value indicating success/failure of the initialization.
        Raises:
            AttributeError:
                AttributeError is raised if the neuron initialization failed
            IndexError:
                IndexError is raised if the hotkey cannot be found from the metagraph
        """
        bt.logging(config=self.neuron_config, logging_dir=self.neuron_config.full_path)
        bt.logging.info(
            f"Initializing validator for subnet: {self.neuron_config.netuid} on network: {self.neuron_config.subtensor.chain_endpoint} with config: {self.neuron_config}"
        )

        # Setup the bittensor objects
        wallet, subtensor, dendrite, metagraph = self.setup_bittensor_objects(
            self.neuron_config
        )

        bt.logging.info(
            f"Bittensor objects initialized:\nMetagraph: {metagraph}\nSubtensor: {subtensor}\nWallet: {wallet}"
        )

        # Validate that the validator has registered to the metagraph correctly
        if not self.validator_validation(metagraph, wallet, subtensor):
            raise IndexError("Unable to find validator key from metagraph")

        # Get the unique identity (UID) from the network
        validator_uid = metagraph.hotkeys.index(wallet.hotkey.ss58_address)
        bt.logging.info(f"Validator is running with UID: {validator_uid}")

        self.wallet = wallet
        self.subtensor = subtensor
        self.dendrite = dendrite
        self.metagraph = metagraph

        # Read command line arguments and perform actions based on them
        args = self._parse_args(parser=self.parser)

        if args:
            if args.load_state == "False":
                self.load_validator_state = False
            else:
                self.load_validator_state = True

            if self.load_validator_state:
                self.load_state()
                self.load_miner_state()
            else:
                self.init_default_scores()

            if args.max_targets:
                self.max_targets = args.max_targets
            else:
                self.max_targets = 256

        else:
            # Setup initial scoring weights
            self.init_default_scores()
            self.max_targets = 256

        self.target_group = 0

        return True

    def _parse_args(self, parser):
        return parser.parse_args()

    def process_responses(
        self,
        processed_uids: torch.tensor,
        query: dict,
        responses: list,
        synapse_uuid: str,
    ) -> list:
        """
        This function processes the responses received from the miners.
        """

        target = query["label"]

        if self.wandb_enabled:
            # Update wandb timestamp for the current run
            self.wandb_handler.set_timestamp()

            # Log target to wandb
            self.wandb_handler.log(data={"Target": target})
            bt.logging.trace(f"Adding wandb logs for target: {target}")

        bt.logging.debug(f"Confidence target set to: {target}")

        # Initiate the response objects
        response_data = []
        responses_invalid_uids = []
        responses_valid_uids = []

        # Check each response
        for i, response in enumerate(responses):
            # Get the hotkey for the response
            hotkey = self.metagraph.hotkeys[processed_uids[i]]

            # Get the default response object
            response_object = scoring.process.get_response_object(
                processed_uids[i], hotkey, target, query["prompt"], synapse_uuid
            )

            # Set the score for invalid responses to 0.0
            if not scoring.process.validate_response(hotkey, response.output):
                self.scores, old_score, unweighted_new_score = (
                    scoring.process.assign_score_for_uid(
                        self.scores,
                        processed_uids[i],
                        self.neuron_config.alpha,
                        0.0,
                        query["weight"],
                    )
                )
                responses_invalid_uids.append(processed_uids[i])

            # Calculate score for valid response
            else:
                response_time = response.dendrite.process_time

                scored_response = self.calculate_score(
                    response.output, target, query["prompt"], response_time, hotkey
                )

                self.scores, old_score, unweighted_new_score = (
                    scoring.process.assign_score_for_uid(
                        self.scores,
                        processed_uids[i],
                        self.neuron_config.alpha,
                        scored_response["scores"]["total"],
                        query["weight"],
                    )
                )

                miner_response = {
                    "prompt": response.output["prompt"],
                    "confidence": response.output["confidence"],
                    "synapse_uuid": response.output["synapse_uuid"],
                    "signature": response.output["signature"],
                    "nonce": response.output["nonce"],
                    "timestamp": response.output["timestamp"],
                }

                text_class = [
                    data
                    for data in response.output["engines"]
                    if data["name"] == "engine:text_classification"
                ]

                vector_search = [
                    data
                    for data in response.output["engines"]
                    if data["name"] == "engine:vector_search"
                ]

                yara = [
                    data
                    for data in response.output["engines"]
                    if data["name"] == "engine:yara"
                ]

                engine_data = []

                if text_class:
                    if len(text_class) > 0:
                        engine_data.append(text_class[0])
                if vector_search:
                    if len(vector_search) > 0:
                        engine_data.append(vector_search[0])
                if yara:
                    if len(yara) > 0:
                        engine_data.append(yara[0])

                responses_valid_uids.append(processed_uids[i])

                if response.output["subnet_version"]:
                    if response.output["subnet_version"] > self.subnet_version:
                        bt.logging.warning(
                            f'Received a response from a miner with higher subnet version ({response.output["subnet_version"]}) than yours ({self.subnet_version}). Please update the validator.'
                        )

                # Populate response data
                response_object["response"] = miner_response
                response_object["engine_data"] = engine_data
                response_object["scored_response"] = scored_response
                response_object["weight_scores"] = {
                    "new": float(self.scores[processed_uids[i]]),
                    "old": float(old_score),
                    "change": float(self.scores[processed_uids[i]]) - float(old_score),
                    "unweighted": unweighted_new_score,
                    "weight": query["weight"],
                }

                if self.wandb_enabled:
                    wandb_logs = [
                        {
                            f"{response_object['UID']}:{response_object['hotkey']}_confidence": response_object[
                                "response"
                            ][
                                "confidence"
                            ]
                        },
                        {
                            f"{response_object['UID']}:{response_object['hotkey']}_scores_total": response_object[
                                "scored_response"
                            ][
                                "scores"
                            ][
                                "total"
                            ]
                        },
                        {
                            f"{response_object['UID']}:{response_object['hotkey']}_scores_distance": response_object[
                                "scored_response"
                            ][
                                "scores"
                            ][
                                "distance"
                            ]
                        },
                        {
                            f"{response_object['UID']}:{response_object['hotkey']}_scores_speed": response_object[
                                "scored_response"
                            ][
                                "scores"
                            ][
                                "speed"
                            ]
                        },
                        {
                            f"{response_object['UID']}:{response_object['hotkey']}_raw_scores_distance": response_object[
                                "scored_response"
                            ][
                                "raw_scores"
                            ][
                                "distance"
                            ]
                        },
                        {
                            f"{response_object['UID']}:{response_object['hotkey']}_raw_scores_speed": response_object[
                                "scored_response"
                            ][
                                "raw_scores"
                            ][
                                "speed"
                            ]
                        },
                        {
                            f"{response_object['UID']}:{response_object['hotkey']}_weight_score_new": response_object[
                                "weight_scores"
                            ][
                                "new"
                            ]
                        },
                        {
                            f"{response_object['UID']}:{response_object['hotkey']}_weight_score_old": response_object[
                                "weight_scores"
                            ][
                                "old"
                            ]
                        },
                        {
                            f"{response_object['UID']}:{response_object['hotkey']}_weight_score_change": response_object[
                                "weight_scores"
                            ][
                                "change"
                            ]
                        },
                    ]

                    for entry in response_object["engine_data"]:
                        wandb_logs.append(
                            {
                                f"{response_object['UID']}:{response_object['hotkey']}_{entry['name']}_confidence": entry[
                                    "confidence"
                                ]
                            },
                        )
                    for wandb_log in wandb_logs:
                        self.wandb_handler.log(wandb_log)

                    bt.logging.trace(
                        f"Adding wandb logs for response data: {wandb_logs} for uid: {processed_uids[i]}"
                    )

            bt.logging.debug(f"Processed response: {response_object}")

            response_data.append(response_object)

        bt.logging.info(f"Received valid responses from UIDs: {responses_valid_uids}")
        bt.logging.info(
            f"Received invalid responses from UIDs: {responses_invalid_uids}"
        )

        return response_data

    def calculate_subscore_speed(self, hotkey, response_time):
        """Calculates the speed subscore for the response"""

        # Calculate score for the speed of the response
        bt.logging.trace(
            f"Calculating speed_score for {hotkey} with response_time: {response_time} and timeout {self.timeout}"
        )
        if response_time > self.timeout:
            bt.logging.debug(
                f"Received response time {response_time} larger than timeout {self.timeout}, setting response_time to timeout value"
            )
            response_time = self.timeout

        speed_score = 1.0 - (response_time / self.timeout)

        return speed_score

    def get_response_penalties(self, response, hotkey, prompt):
        """This function resolves the penalties for the response"""

        similarity_penalty, base_penalty, duplicate_penalty = self.apply_penalty(
            response, hotkey, prompt
        )

        distance_penalty_multiplier = 1.0
        speed_penalty = 1.0

        if base_penalty >= 20:
            distance_penalty_multiplier = 0.0
        elif base_penalty > 0.0:
            distance_penalty_multiplier = 1 - ((base_penalty / 2.0) / 10)

        if sum([similarity_penalty, duplicate_penalty]) >= 20:
            speed_penalty = 0.0
        elif sum([similarity_penalty, duplicate_penalty]) > 0.0:
            speed_penalty = 1 - (
                ((sum([similarity_penalty, duplicate_penalty])) / 2.0) / 10
            )

        return distance_penalty_multiplier, speed_penalty

    def calculate_penalized_scores(
        self,
        score_weights,
        distance_score,
        speed_score,
        distance_penalty,
        speed_penalty,
    ):
        """Applies the penalties to the score and calculates the final score"""

        final_distance_score = (
            score_weights["distance"] * distance_score
        ) * distance_penalty
        final_speed_score = (score_weights["speed"] * speed_score) * speed_penalty

        total_score = final_distance_score + final_speed_score

        return total_score, final_distance_score, final_speed_score

    def calculate_score(
        self, response, target: float, prompt: str, response_time: float, hotkey: str
    ) -> dict:
        """This function sets the score based on the response.

        Returns:
            score:
                An instance of dict containing the scoring information for a response
        """

        # Calculate distance score
        distance_score = scoring.process.calculate_subscore_distance(response, target)
        if distance_score is None:
            bt.logging.debug(
                f"Received an invalid response: {response} from hotkey: {hotkey}"
            )
            distance_score = 0.0

        # Calculate speed score
        speed_score = scoring.process.calculate_subscore_speed(
            self.timeout, response_time
        )
        if speed_score is None:
            bt.logging.debug(
                f"Response time {response_time} was larger than timeout {self.timeout} for response: {response} from hotkey: {hotkey}"
            )
            speed_score = 0.0

        # Validate individual scores
        if not validate_numerical_value(
            distance_score, float, 0.0, 1.0
        ) or not validate_numerical_value(speed_score, float, 0.0, 1.0):
            bt.logging.error(
                f"Calculated out-of-bounds individual scores (Distance: {distance_score} - Speed: {speed_score}) for the response: {response} from hotkey: {hotkey}"
            )
            return scoring.process.get_engine_response_object()

        # Set weights for scores
        score_weights = {"distance": 0.85, "speed": 0.15}

        # Get penalty multipliers
        distance_penalty, speed_penalty = self.get_response_penalties(
            response, hotkey, prompt
        )

        # Apply penalties to scores
        (
            total_score,
            final_distance_score,
            final_speed_score,
        ) = self.calculate_penalized_scores(
            score_weights, distance_score, speed_score, distance_penalty, speed_penalty
        )

        # Validate individual scores
        if (
            not validate_numerical_value(total_score, float, 0.0, 1.0)
            or not validate_numerical_value(final_distance_score, float, 0.0, 1.0)
            or not validate_numerical_value(final_speed_score, float, 0.0, 1.0)
        ):
            bt.logging.error(
                f"Calculated out-of-bounds individual scores (Total: {total_score} - Distance: {final_distance_score} - Speed: {final_speed_score}) for the response: {response} from hotkey: {hotkey}"
            )
            return scoring.process.get_engine_response_object()

        # Log the scoring data
        score_logger = {
            "hotkey": hotkey,
            "prompt": prompt,
            "target": target,
            "synapse_uuid": response["synapse_uuid"],
            "score_weights": score_weights,
            "penalties": {"distance": distance_penalty, "speed": speed_penalty},
            "raw_scores": {"distance": distance_score, "speed": speed_score},
            "final_scores": {
                "total": total_score,
                "distance": final_distance_score,
                "speed": final_speed_score,
            },
        }

        bt.logging.debug(f"Calculated score: {score_logger}")

        return scoring.process.get_engine_response_object(
            total_score=total_score,
            final_distance_score=final_distance_score,
            final_speed_score=final_speed_score,
            distance_penalty=distance_penalty,
            speed_penalty=speed_penalty,
            raw_distance_score=distance_score,
            raw_speed_score=speed_score,
        )

    def apply_penalty(self, response, hotkey, prompt) -> tuple:
        """
        Applies a penalty score based on the response and previous
        responses received from the miner.
        """

        # If hotkey is not found from list of responses, penalties
        # cannot be calculated.
        if not self.miner_responses:
            return 5.0, 5.0, 5.0
        if not hotkey in self.miner_responses.keys():
            return 5.0, 5.0, 5.0

        # Get UID
        uid = self.metagraph.hotkeys.index(hotkey)

        similarity = base = duplicate = 0.0
        # penalty_score -= confidence.check_penalty(self.miner_responses["hotkey"], response)
        similarity += penalty.similarity.check_penalty(
            uid, self.miner_responses[hotkey]
        )
        base += penalty.base.check_penalty(
            uid, self.miner_responses[hotkey], response, prompt
        )
        duplicate += penalty.duplicate.check_penalty(
            uid, self.miner_responses[hotkey], response
        )

        bt.logging.trace(
            f"Penalty score {[similarity, base, duplicate]} for response '{response}' from UID '{uid}'"
        )
        return similarity, base, duplicate

    def get_api_prompt(self, hotkey, signature, synapse_uuid, timestamp, nonce) -> dict:
        """Retrieves a prompt from the prompt API"""

        headers = {
            "X-Hotkey": hotkey,
            "X-Signature": signature,
            "X-SynapseUUID": synapse_uuid,
            "X-Timestamp": timestamp,
            "X-Nonce": nonce
        }

        prompt_api_url = "https://api.synapsec.ai/prompt"

        try:
            # get prompt
            res = requests.post(url=prompt_api_url, headers=headers, data={}, timeout=6)
            # check for correct status code
            if res.status_code == 200:
                # get prompt entry from the API output
                prompt_entry = res.json()
                # check to make sure prompt is valid
                bt.logging.trace(
                    f"Loaded remote prompt to serve to miners: {prompt_entry}"
                )
                return prompt_entry

            else:
                bt.logging.warning(
                    f"Unable to get prompt from the Prompt API: HTTP/{res.status_code} - {res.json()}"
                )
        except requests.exceptions.ReadTimeout as e:
            bt.logging.error(f"Prompt API request timed out: {e}")
        except requests.exceptions.JSONDecodeError as e:
            bt.logging.error(f"Unable to read the response from the prompt API: {e}")
        except requests.exceptions.ConnectionError as e:
            bt.logging.error(f"Unable to connect to the prompt API: {e}")
        except Exception as e:
            bt.logging.error(f'Generic error during request: {e}')

    def get_local_prompt(self, hotkey, synapse_uuid):
        try:
            # Get the old dataset if the API cannot be called for some reason
            entry = mock_data.get_prompt(hotkey, synapse_uuid)
            return entry
        except Exception as e:
            raise RuntimeError(
                f"Unable to retrieve a prompt from the API and from local database: {e}"
            ) from e

    def serve_prompt(self, synapse_uuid) -> dict:
        """Generates a prompt to serve to a miner

        This function queries a prompt from the API, and if the API
        fails for some reason it selects a random prompt from the local dataset
        to be served for the miners connected to the subnet.

        Args:
            None

        Returns:
            entry:
                A dict instance
        """
        if self.target_group == 0:
            # Attempt to get prompt from prompt API
            nonce = str(secrets.token_hex(24))
            timestamp = str(int(time.time()))

            data = f'{synapse_uuid}{nonce}{timestamp}'

            entry = self.get_api_prompt(
                hotkey=self.wallet.hotkey.ss58_address,
                signature=sign_data(wallet=self.wallet, data=data),
                synapse_uuid=synapse_uuid, timestamp=timestamp, nonce=nonce
            )
            if not validate_prompt(entry):
                bt.logging.warning(
                    f"Received prompt from prompt API '{entry}' but the validation failed. Using local prompt instead."
                )
                self.prompt = self.get_local_prompt(
                    hotkey = self.wallet.hotkey.ss58_address, 
                    synapse_uuid = synapse_uuid
                )
            else:
                self.prompt = entry

        return self.prompt

    def check_hotkeys(self):
        """Checks if some hotkeys have been replaced in the metagraph"""
        if self.hotkeys:
            # Check if known state len matches with current metagraph hotkey length
            if len(self.hotkeys) == len(self.metagraph.hotkeys):
                current_hotkeys = self.metagraph.hotkeys
                for i, hotkey in enumerate(current_hotkeys):
                    if self.hotkeys[i] != hotkey:
                        bt.logging.debug(
                            f"Index '{i}' has mismatching hotkey. Old hotkey: '{self.hotkeys[i]}', new hotkey: '{hotkey}. Resetting score to 0.0"
                        )
                        bt.logging.debug(f"Score before reset: {self.scores[i]}")
                        self.scores[i] = 0.0
                        bt.logging.debug(f"Score after reset: {self.scores[i]}")
            else:
                # Init default scores
                bt.logging.info(
                    f"Init default scores because of state and metagraph hotkey length mismatch. Expected: {len(self.metagraph.hotkeys)} had: {len(self.hotkeys)}"
                )
                self.init_default_scores()

            self.hotkeys = copy.deepcopy(self.metagraph.hotkeys)
        else:
            self.hotkeys = copy.deepcopy(self.metagraph.hotkeys)

    def save_miner_state(self):
        """Saves the miner state to a file."""
        with open(f"{self.base_path}/miners.pickle", "wb") as pickle_file:
            pickle.dump(self.miner_responses, pickle_file)

        bt.logging.debug("Saved miner states to a file")

    def load_miner_state(self):
        """Loads the miner state from a file"""
        state_path = f"{self.base_path}/miners.pickle"
        if path.exists(state_path):
            try:
                with open(state_path, "rb") as pickle_file:
                    self.miner_responses = pickle.load(pickle_file)

                bt.logging.debug("Loaded miner state from a file")
            except Exception as e:
                bt.logging.error(
                    f"Miner response data reset because a failure to read the miner response data, error: {e}"
                )

                # Rename the current miner state file if exception
                # occurs and reset the default state
                rename(
                    state_path,
                    f"{state_path}-{int(datetime.now().timestamp())}.autorecovery",
                )
                self.miner_responses = None

    def truncate_miner_state(self):
        """Truncates the local miner state"""

        if self.miner_responses:
            old_size = getsizeof(self.miner_responses) + sum(
                getsizeof(key) + getsizeof(value)
                for key, value in self.miner_responses.items()
            )
            for hotkey in self.miner_responses:
                self.miner_responses[hotkey] = self.miner_responses[hotkey][-100:]

            bt.logging.debug(
                f"Truncated miner response list (Old: '{old_size}' - New: '{getsizeof(self.miner_responses) + sum(getsizeof(key) + getsizeof(value) for key, value in self.miner_responses.items())}')"
            )

    def save_state(self):
        """Saves the state of the validator to a file."""
        bt.logging.info("Saving validator state.")

        # Save the state of the validator to file.
        torch.save(
            {
                "step": self.step,
                "scores": self.scores,
                "hotkeys": self.hotkeys,
                "last_updated_block": self.last_updated_block,
                "blacklisted_miner_hotkeys": self.blacklisted_miner_hotkeys,
            },
            self.base_path + "/state.pt",
        )

        bt.logging.debug(
            f"Saved the following state to a file: step: {self.step}, scores: {self.scores}, hotkeys: {self.hotkeys}, last_updated_block: {self.last_updated_block}, blacklisted_miner_hotkeys: {self.blacklisted_miner_hotkeys}"
        )

    def init_default_scores(self) -> None:
        """Validators without previous validation knowledge should start
        with default score of 0.0 for each UID. The method can also be
        used to reset the scores in case of an internal error"""

        bt.logging.info("Initiating validator with default scores for each UID")
        self.scores = torch.zeros_like(self.metagraph.S, dtype=torch.float32)
        bt.logging.info(f"Validation weights have been initialized: {self.scores}")

    def reset_validator_state(self, state_path):
        """Inits the default validator state. Should be invoked only
        when an exception occurs and the state needs to reset."""

        # Rename current state file in case manual recovery is needed
        rename(
            state_path,
            f"{state_path}-{int(datetime.now().timestamp())}.autorecovery",
        )

        self.init_default_scores()
        self.step = 0
        self.last_updated_block = 0
        self.hotkeys = None
        self.blacklisted_miner_hotkeys = None

    def load_state(self):
        """Loads the state of the validator from a file."""

        # Load the state of the validator from file.
        state_path = self.base_path + "/state.pt"
        if path.exists(state_path):
            try:
                bt.logging.info("Loading validator state.")
                state = torch.load(state_path)
                bt.logging.debug(f"Loaded the following state from file: {state}")
                self.step = state["step"]
                self.scores = state["scores"]
                self.hotkeys = state["hotkeys"]
                self.last_updated_block = state["last_updated_block"]
                if "blacklisted_miner_hotkeys" in state.keys():
                    self.blacklisted_miner_hotkeys = state["blacklisted_miner_hotkeys"]

                bt.logging.info(f"Scores loaded from saved file: {self.scores}")
            except Exception as e:
                bt.logging.error(
                    f"Validator state reset because an exception occurred: {e}"
                )
                self.reset_validator_state(state_path=state_path)

        else:
            self.init_default_scores()

    @timeout_decorator(timeout=30)
    def sync_metagraph(self, metagraph, subtensor):
        """Syncs the metagraph"""

        bt.logging.debug(
            f"Syncing metagraph: {self.metagraph} with subtensor: {self.subtensor}"
        )

        # Sync the metagraph
        metagraph.sync(subtensor=subtensor)

        return metagraph

    @timeout_decorator(timeout=30)
    def set_weights(self):
        """Sets the weights for the subnet"""

        weights = torch.nn.functional.normalize(self.scores, p=1.0, dim=0)
        bt.logging.info(f"Setting weights: {weights}")

        bt.logging.debug(
            f"Setting weights with the following parameters: netuid={self.neuron_config.netuid}, wallet={self.wallet}, uids={self.metagraph.uids}, weights={weights}, version_key={self.subnet_version}"
        )
        # This is a crucial step that updates the incentive mechanism on the Bittensor blockchain.
        # Miners with higher scores (or weights) receive a larger share of TAO rewards on this subnet.
        result = self.subtensor.set_weights(
            netuid=self.neuron_config.netuid,  # Subnet to set weights on.
            wallet=self.wallet,  # Wallet to sign set weights using hotkey.
            uids=self.metagraph.uids,  # Uids of the miners to set weights for.
            weights=weights,  # Weights to set for the miners.
            wait_for_inclusion=False,
            version_key=self.subnet_version,
        )
        if result:
            bt.logging.success("Successfully set weights.")
        else:
            bt.logging.error("Failed to set weights.")

    def _get_local_miner_blacklist(self) -> list:
        """Returns the blacklisted miners hotkeys from the local file."""

        # Check if local blacklist exists
        blacklist_file = f"{self.base_path}/miner_blacklist.json"
        if Path(blacklist_file).is_file():
            # Load the contents of the local blaclist
            bt.logging.trace(f"Reading local blacklist file: {blacklist_file}")
            try:
                with open(blacklist_file, "r", encoding="utf-8") as file:
                    file_content = file.read()

                miner_blacklist = json.loads(file_content)
                if validate_miner_blacklist(miner_blacklist):
                    bt.logging.trace(f"Loaded miner blacklist: {miner_blacklist}")
                    return miner_blacklist

                bt.logging.trace(
                    f"Loaded miner blacklist was formatted incorrectly or was empty: {miner_blacklist}"
                )
            except OSError as e:
                bt.logging.error(f"Unable to read blacklist file: {e}")
            except json.JSONDecodeError as e:
                bt.logging.error(
                    f"Unable to parse JSON from path: {blacklist_file} with error: {e}"
                )
        else:
            bt.logging.trace(f"No local miner blacklist file in path: {blacklist_file}")

        return []

    def _get_remote_miner_blacklist(self) -> list:
        """Retrieves the remote blacklist"""

        blacklist_api_url = "https://ujetecvbvi.execute-api.eu-west-1.amazonaws.com/default/sn14-blacklist-api"

        try:
            res = requests.get(url=blacklist_api_url, timeout=12)
            if res.status_code == 200:
                miner_blacklist = res.json()
                if validate_miner_blacklist(miner_blacklist):
                    bt.logging.trace(
                        f"Loaded remote miner blacklist: {miner_blacklist}"
                    )
                    return miner_blacklist
                bt.logging.trace(
                    f"Remote miner blacklist was formatted incorrectly or was empty: {miner_blacklist}"
                )

            else:
                bt.logging.warning(
                    f"Miner blacklist API returned unexpected status code: {res.status_code}"
                )
        except requests.exceptions.ReadTimeout as e:
            bt.logging.error(f"Request timed out: {e}")
        except requests.exceptions.JSONDecodeError as e:
            bt.logging.error(f"Unable to read the response from the API: {e}")
        except requests.exceptions.ConnectionError as e:
            bt.logging.error(f"Unable to connect to the blacklist API: {e}")
        except Exception as e:
            bt.logging.error(f'Generic error during request: {e}')

        return []

    def check_blacklisted_miner_hotkeys(self):
        """Combines local and remote miner blacklists and returns list of hotkeys"""

        miner_blacklist = (
            self._get_local_miner_blacklist() + self._get_remote_miner_blacklist()
        )

        self.blacklisted_miner_hotkeys = [
            item["hotkey"] for item in miner_blacklist if "hotkey" in item
        ]

    def get_uids_to_query(self, all_axons) -> list:
        """Returns the list of UIDs to query"""

        # Get UIDs with a positive stake
        uids_with_stake = self.metagraph.total_stake >= 0.0
        bt.logging.trace(f"UIDs with a positive stake: {uids_with_stake}")

        # Get UIDs with an IP address of 0.0.0.0
        invalid_uids = torch.tensor(
            [
                bool(value)
                for value in [
                    ip != "0.0.0.0"
                    for ip in [
                        self.metagraph.neurons[uid].axon_info.ip
                        for uid in self.metagraph.uids.tolist()
                    ]
                ]
            ],
            dtype=torch.bool,
        )
        bt.logging.trace(f"UIDs with 0.0.0.0 as an IP address: {invalid_uids}")

        # Get UIDs that have their hotkey blacklisted
        blacklisted_uids = []
        if self.blacklisted_miner_hotkeys:
            for hotkey in self.blacklisted_miner_hotkeys:
                if hotkey in self.metagraph.hotkeys:
                    blacklisted_uids.append(self.metagraph.hotkeys.index(hotkey))
                else:
                    bt.logging.trace(
                        f"Blacklisted hotkey {hotkey} was not found from metagraph"
                    )

            bt.logging.debug(f"Blacklisted the following UIDs: {blacklisted_uids}")

        # Convert blacklisted UIDs to tensor
        blacklisted_uids_tensor = torch.tensor(
            [uid not in blacklisted_uids for uid in self.metagraph.uids.tolist()],
            dtype=torch.bool,
        )

        bt.logging.trace(f"Blacklisted UIDs: {blacklisted_uids_tensor}")

        # Determine the UIDs to filter
        uids_to_filter = torch.logical_not(
            ~blacklisted_uids_tensor | ~invalid_uids | ~uids_with_stake
        )

        bt.logging.trace(f"UIDs to filter: {uids_to_filter}")

        # Define UIDs to query
        uids_to_query = [
            axon
            for axon, keep_flag in zip(all_axons, uids_to_filter)
            if keep_flag.item()
        ]

        # Define UIDs to filter
        final_axons_to_filter = [
            axon
            for axon, keep_flag in zip(all_axons, uids_to_filter)
            if not keep_flag.item()
        ]

        uids_not_to_query = [
            self.metagraph.hotkeys.index(axon.hotkey) for axon in final_axons_to_filter
        ]

        bt.logging.trace(f"Final axons to filter: {final_axons_to_filter}")
        bt.logging.debug(f"Filtered UIDs: {uids_not_to_query}")

        # Reduce the number of simultaneous UIDs to query
        if self.max_targets < 256:
            start_idx = self.max_targets * self.target_group
            end_idx = min(
                len(uids_to_query), self.max_targets * (self.target_group + 1)
            )
            if start_idx == end_idx:
                return [], []
            if start_idx >= len(uids_to_query):
                raise IndexError(
                    "Starting index for querying the miners is out-of-bounds"
                )

            if end_idx >= len(uids_to_query):
                end_idx = len(uids_to_query)
                self.target_group = 0
            else:
                self.target_group += 1

            bt.logging.debug(
                f"List indices for UIDs to query starting from: '{start_idx}' ending with: '{end_idx}'"
            )
            uids_to_query = uids_to_query[start_idx:end_idx]

        list_of_uids = [
            self.metagraph.hotkeys.index(axon.hotkey) for axon in uids_to_query
        ]

        list_of_hotkeys = [axon.hotkey for axon in uids_to_query]

        bt.logging.trace(f"Sending query to the following hotkeys: {list_of_hotkeys}")

        return uids_to_query, list_of_uids, blacklisted_uids, uids_not_to_query
