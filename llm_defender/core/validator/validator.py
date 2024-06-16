"""Module for prompt-injection neurons for the
llm-defender-subnet.

Long description

Typical example usage:

    foo = bar()
    foo.bar()
"""

import asyncio
import copy
import pickle
from argparse import ArgumentParser
from typing import Tuple
from sys import getsizeof
from datetime import datetime
from os import path, rename
import secrets
import time
import bittensor as bt
import requests
import numpy as np
from collections import defaultdict 

# Import custom modules
import llm_defender.base as LLMDefenderBase
import llm_defender.core.validator as LLMDefenderCore
from .sensitive_information.generation.generator import SensitiveInfoGenerator

class SubnetValidator(LLMDefenderBase.BaseNeuron):
    """Summary of the class

    Class description

    Attributes:

    """

    def __init__(self, parser: ArgumentParser):
        super().__init__(parser=parser, profile="validator")
        
        self.timeout = 6
        self.neuron_config = None
        self.wallet = None
        self.subtensor = None
        self.dendrite = None
        self.metagraph: bt.metagraph | None = None
        self.scores = None
        self.prompt_injection_scores = None
        self.sensitive_information_scores = None
        self.hotkeys = None
        self.miner_responses = {}
        self.max_targets = None
        self.target_group = None
        self.load_validator_state = None
        self.prompt = None
        self.query = None
        self.debug_mode = True
        self.sensitive_info_generator = SensitiveInfoGenerator()

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
        # Read command line arguments and perform actions based on them
        args = self._parse_args(parser=self.parser)

        # Setup logging
        bt.logging(config=self.neuron_config, logging_dir=self.neuron_config.full_path)
        if args.log_level == "DEBUG":
            bt.logging.enable_debug()
        elif args.log_level == "TRACE":
            bt.logging.enable_trace()
        else:
            bt.logging.enable_default()
        
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

        if not args or not args.debug_mode:
            # Validate that the validator has registered to the metagraph correctly
            if not self.validator_validation(metagraph, wallet, subtensor):
                raise IndexError("Unable to find validator key from metagraph")

            # Get the unique identity (UID) from the network
            validator_uid = metagraph.hotkeys.index(wallet.hotkey.ss58_address)
            bt.logging.info(f"Validator is running with UID: {validator_uid}")

            # Disable debug mode
            self.debug_mode = False

        self.wallet = wallet
        self.subtensor = subtensor
        self.dendrite = dendrite
        self.metagraph = metagraph

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

    async def send_metrics_synapse(self, response_object, synapse_uuid, target_uid):
        """This method sends a synapse to the target_uid containing the
        response_object"""

        # Generate signature
        nonce = secrets.token_hex(24)
        timestamp = str(int(time.time()))
        data_to_sign = (
            f"{synapse_uuid}{nonce}{self.wallet.hotkey.ss58_address}{timestamp}"
        )

        # Send Synapse
        await self.dendrite.forward(
            self.metagraph.axons[target_uid],
            LLMDefenderBase.MetricsProtocol(
                response_object=response_object,
                synapse_uuid=synapse_uuid,
                synapse_nonce=nonce,
                synapse_timestamp=timestamp,
                synapse_signature=LLMDefenderBase.sign_data(
                    hotkey=self.wallet.hotkey, data=data_to_sign
                ),
            ),
            timeout=2,
            deserialize=False
        )

        bt.logging.debug(f'Metrics synapse processed for UUID: {synapse_uuid} and UID: {target_uid}')

    def _parse_args(self, parser):
        return parser.parse_args()

    async def process_responses(
        self,
        processed_uids: np.ndarray,
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

        # Collect tasks in a set
        background_tasks = set()

        # Check each response
        for i, response in enumerate(responses):
            if query["analyzer"] == "Prompt Injection":
                response_object, responses_invalid_uids, responses_valid_uids = (
                    LLMDefenderCore.prompt_injection_process.process_response(
                        prompt=query["prompt"],
                        response=response,
                        uid=processed_uids[i],
                        target=target,
                        synapse_uuid=synapse_uuid,
                        query=query,
                        validator=self,
                        responses_invalid_uids=responses_invalid_uids,
                        responses_valid_uids=responses_valid_uids,
                    )
                )
            elif query["analyzer"] == "Sensitive Information":
                response_object, responses_invalid_uids, responses_valid_uids = (
                    LLMDefenderCore.sensitive_information_process.process_response(
                        prompt=query["prompt"],
                        response=response,
                        uid=processed_uids[i],
                        target=target,
                        synapse_uuid=synapse_uuid,
                        query=query,
                        validator=self,
                        responses_invalid_uids=responses_invalid_uids,
                        responses_valid_uids=responses_valid_uids,
                    )
                )
            else:
                bt.logging.error(f"Received unsupported analyzer: {query}")
                raise AttributeError(f"Received unsupported analyzer: {query}")

            # Handle response
            response_data.append(response_object)
            if response_object["response"]:
                # Add asyncio task to background tasks
                task = asyncio.create_task(self.send_metrics_synapse(response_object=response_object, synapse_uuid=synapse_uuid, target_uid=processed_uids[i]))
                background_tasks.add(task)
        
        # Handle background tasks
        try:
            for task in background_tasks:
                await task
        except Exception as e:
            bt.logging.error(f'Error while handling background tasks for metric synapses: {e}')
    

        bt.logging.info(f"Received valid responses from UIDs: {responses_valid_uids}")
        bt.logging.info(
            f"Received invalid responses from UIDs: {responses_invalid_uids}"
        )

        return response_data
    

    def determine_overall_scores(
        self, specialization_bonus_n=5
    ):

        top_prompt_injection_uids = np.argsort(self.prompt_injection_scores)[-specialization_bonus_n:][::-1]
        bt.logging.trace(f"Top {specialization_bonus_n} Miner UIDs for the Prompt Injection Analyzer: {top_prompt_injection_uids}")
        top_sensitive_information_uids = np.argsort(self.sensitive_information_scores)[-specialization_bonus_n:][::-1]
        bt.logging.trace(f"Top {specialization_bonus_n} Miner UIDs for the Sensitive Information Analyzer: {top_sensitive_information_uids}")

        for uid, _ in enumerate(self.scores):

            analyzer_avg = (
                self.prompt_injection_scores[uid]
                + self.sensitive_information_scores[uid]
            ) / 2
            self.scores[uid] = analyzer_avg

            top_prompt_injection_uid = 0
            top_sensitive_informaiton_uid = 0

            if uid in top_prompt_injection_uids:
                top_prompt_injection_uid = 1
                if self.prompt_injection_scores[uid] > self.scores[uid]:
                    self.scores[uid] = self.prompt_injection_scores[uid]

            if uid in top_sensitive_information_uids:
                top_sensitive_informaiton_uid = 1
                if self.sensitive_information_scores[uid] > self.scores[uid]:
                    self.scores[uid] = self.sensitive_information_scores[uid]

            miner_hotkey = self.metagraph.hotkeys[uid]

            if self.wandb_enabled:
                wandb_logs = [
                    {
                        f"{uid}:{miner_hotkey}_is_top_prompt_injection_uid": top_prompt_injection_uid
                    },
                    {
                        f"{uid}:{miner_hotkey}_is_top_sensitive_information_uid": top_sensitive_informaiton_uid
                    },
                    {f"{uid}:{miner_hotkey}_total_score": self.scores[uid]},
                ]

                for wandb_log in wandb_logs:
                    self.wandb_handler.log(wandb_log)

        bt.logging.trace(f"Calculated miner scores: {self.scores}")

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

    def get_api_prompt(self, hotkey, signature, synapse_uuid, timestamp, nonce) -> dict:
        """Retrieves a prompt from the prompt API"""

        headers = {
            "X-Hotkey": hotkey,
            "X-Signature": signature,
            "X-SynapseUUID": synapse_uuid,
            "X-Timestamp": timestamp,
            "X-Nonce": nonce,
            "X-Version": str(self.subnet_version),
            "X-API-Key": hotkey,
        }

        prompt_api_url = "https://api.synapsec.ai/prompt"

        try:
            # get prompt
            res = requests.post(url=prompt_api_url, headers=headers, timeout=12)
            # check for correct status code
            if res.status_code == 200:
                # get prompt entry from the API output
                prompt_entry = res.json()
                # check to make sure prompt is valid
                if LLMDefenderBase.validate_validator_api_prompt_output(prompt_entry):
                    bt.logging.trace(
                        f"Loaded remote prompt to serve to miners: {prompt_entry}"
                    )
                    return prompt_entry
                else:
                    return None

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
            bt.logging.error(f"Generic error during request: {e}")

        return {}

    def serve_prompt_injection_prompt(self, synapse_uuid) -> dict:
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
        # Attempt to get prompt from prompt API
        nonce = str(secrets.token_hex(24))
        timestamp = str(int(time.time()))

        data = f"{synapse_uuid}{nonce}{timestamp}"

        entry = self.get_api_prompt(
            hotkey=self.wallet.hotkey.ss58_address,
            signature=LLMDefenderBase.sign_data(hotkey=self.wallet.hotkey, data=data),
            synapse_uuid=synapse_uuid,
            timestamp=timestamp,
            nonce=nonce,
        )

        self.prompt = entry

        return self.prompt
    
    def serve_sensitive_information_prompt(self):
        prompt, category, target = self.sensitive_info_generator.get_prompt_to_serve_miners()
        return {
            "prompt":prompt,
            "analyzer":'Sensitive Information',
            "category":category,
            "label":target,
            "weight": 1.0
        }

    async def load_prompt_to_validator_async(self, synapse_uuid, analyzer):
        if analyzer == 'Prompt Injection':
            return await asyncio.to_thread(self.serve_prompt_injection_prompt)
        elif analyzer == 'Sensitive Information':
            return await asyncio.to_thread(self.serve_sensitive_information_prompt)

    def check_hotkeys(self):
        """Checks if some hotkeys have been replaced in the metagraph"""
        if self.hotkeys is None:
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
        with open(
            f"{self.cache_path}/miners.pickle", "wb"
        ) as pickle_file:
            pickle.dump(self.miner_responses, pickle_file)

        filename = f"{self.cache_path}/miners.pickle"
        bt.logging.debug(f"Saved miner states to file: {filename}")

    def check_miner_responses_are_formatted_correctly(self, miner_responses):

        correct_formatting = True 

        needed_keys_response = [
            "UID", "coldkey", "hotkey", 
            "target", "prompt", "analyzer", 
            "category", "synapse_uuid", "response",
            "scored_response", "engine_data"
        ]

        needed_keys_scored_response = [
            "scores", "raw_scores", "penalties"
        ]

        needed_keys_scores = [
            "binned_distance_score", "total_analyzer_raw", "normalized_distance_score",
            "distance", "speed"
        ]   

        for _, responses in miner_responses.items():
            for response in responses:

                response_keys = [k for k in response]
                
                for response_key in response_keys:

                    if response_key not in needed_keys_response:
                        correct_formatting = False
                        break

                    if response_key == "scored_response":

                        scored_response_keys = [k for k in response["scored_response"]]

                        for scored_response_key in scored_response_keys:

                            if scored_response_key not in needed_keys_scored_response:
                                correct_formatting = False 
                                break

                            if scored_response_key == "scores":

                                scores_keys = [k for k in response["scored_response"]['scores']]

                                for scores_key in scores_keys:
                                    
                                    if scores_key not in needed_keys_scores:
                                        correct_formatting = False 
                                        break

        return correct_formatting

    def load_miner_state(self):
        """Loads the miner state from a file"""
        state_path = f"{self.cache_path}/miners.pickle"
        if path.exists(state_path):
            try:
                with open(state_path, "rb") as pickle_file:
                    miner_responses = pickle.load(pickle_file)
                    if self.check_miner_responses_are_formatted_correctly(miner_responses):
                        self.miner_responses = miner_responses
                        self.truncate_miner_state(100)
                    else:
                        rename(
                            state_path,
                            f"{state_path}-{int(datetime.now().timestamp())}.autorecovery",
                        )
                        self.miner_responses = {}

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
                self.miner_responses = {}

    def truncate_miner_state(self, max_number_of_responses_per_miner: int):
        if self.miner_responses:

            for hotkey, data_list in self.miner_responses.items():
                analyzer_dict = defaultdict(list)
                
                # Group entries by analyzer type
                for entry in data_list:
                    analyzer_type = entry["analyzer"]
                    analyzer_dict[analyzer_type].append(entry)
                
                # Truncate each analyzer's list to 100 entries
                truncated_list = []
                for analyzer_type, entries in analyzer_dict.items():
                    truncated_list.extend(entries[-max_number_of_responses_per_miner:])
                
                # Update the original list with the truncated list
                self.miner_responses[hotkey] = truncated_list

    def save_state(self):
        """Saves the state of the validator to a file."""
        bt.logging.info("Saving validator state.")

        # Save the state of the validator to file.
        np.savez_compressed(
            f"{self.cache_path}/state.npz",
            step=self.step,
            scores=self.scores,
            prompt_injection_scores=self.prompt_injection_scores,
            sensitive_information_scores=self.sensitive_information_scores,
            hotkeys=self.hotkeys,
            last_updated_block=self.last_updated_block,
        )

        filename = f"{self.cache_path}/state.npz"
        bt.logging.debug(
            f"Saved the following state to file: {filename} step: {self.step}, scores: {self.scores}, prompt_injection_scores: {self.prompt_injection_scores}, sensitive_information_scores: {self.sensitive_information_scores}, hotkeys: {self.hotkeys}, last_updated_block: {self.last_updated_block}"
        )

    def init_default_scores(self) -> None:
        """Validators without previous validation knowledge should start
        with default score of 0.0 for each UID. The method can also be
        used to reset the scores in case of an internal error"""

        bt.logging.info(
            "Initiating validator with default Prompt Injection Analyzer scores for each UID"
        )
        self.prompt_injection_scores = np.zeros_like(self.metagraph.S, dtype=np.float32)
        bt.logging.info(
            f"Prompt Injection Analyzer weights for validation have been initialized: {self.prompt_injection_scores}"
        )

        bt.logging.info(
            "Initiating validator with default Sensiive Information Analyzer scores for each UID"
        )
        self.sensitive_information_scores = np.zeros_like(self.metagraph.S, dtype=np.float32)
        bt.logging.info(
            f"Sensitive Information Analyzer weights for validation have been initialized: {self.sensitive_information_scores}"
        )

        bt.logging.info("Initiating validator with default overall scores for each UID")
        self.scores = np.zeros_like(self.metagraph.S, dtype=np.float32)
        bt.logging.info(
            f"Overall weights for validation have been initialized: {self.scores}"
        )

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

    def load_state(self):
        """Loads the state of the validator from a file."""

        # Load the state of the validator from file.
        state_path = f"{self.cache_path}/state.npz"

        if path.exists(state_path):
            try:
                bt.logging.info("Loading validator state.")
                state = np.load(state_path)
                bt.logging.debug(f"Loaded the following state from file: {state}")
                self.step = state["step"]
                self.scores = state["scores"]

                try:
                    self.prompt_injection_scores = state["prompt_injection_scores"]
                    self.sensitive_information_scores = state[
                        "sensitive_information_scores"
                    ]
                   
                except Exception as e:
                    self.prompt_injection_scores = np.zeros_like(self.metagraph.S, dtype=np.float32)
                    self.sensitive_information_scores = np.zeros_like(self.metagraph.S, dtype=np.float32)

                self.hotkeys = state["hotkeys"]
                self.last_updated_block = state["last_updated_block"]
                bt.logging.info(f"Scores loaded from saved file: {self.scores}")
            except Exception as e:
                bt.logging.error(
                    f"Validator state reset because an exception occurred: {e}"
                )
                self.reset_validator_state(state_path=state_path)
        else:
            self.init_default_scores()

    @LLMDefenderBase.timeout_decorator(timeout=30)
    async def sync_metagraph(self, metagraph, subtensor):
        """Syncs the metagraph"""

        bt.logging.debug(
            f"Syncing metagraph: {self.metagraph} with subtensor: {self.subtensor}"
        )

        # Sync the metagraph
        metagraph.sync(subtensor=subtensor)

        return metagraph

    @LLMDefenderBase.timeout_decorator(timeout=30)
    async def set_weights(self):
        """Sets the weights for the subnet"""

        def power_scaling(scores, power=10):
            transformed_scores = np.power(scores, power)
            normalized_scores = (transformed_scores - transformed_scores.min()) / (transformed_scores.max() - transformed_scores.min())
            return normalized_scores

        weights = power_scaling(self.scores)

        
        
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

    def determine_valid_axons(self, axons):
        """This function determines valid axon to send the query to--
        they must have valid ips """
        # Clear axons that do not have an IP
        axons_with_valid_ip = [axon for axon in axons if axon.ip != "0.0.0.0"]

        # Clear axons with duplicate IP/Port 
        axon_ips = set()
        filtered_axons = [
            axon
            for axon in axons_with_valid_ip
            if axon.ip_str() not in axon_ips and not axon_ips.add(axon.ip_str())
        ]

        bt.logging.debug(
            f"Filtered out axons. Original list: {len(axons)}, filtered list: {len(filtered_axons)}"
        )

        return filtered_axons

    def get_uids_to_query(self, all_axons) -> list:
        """Returns the list of UIDs to query"""

        # Filter Axons with invalid IPs
        valid_axons = self.determine_valid_axons(all_axons)

        # Determine list of Axons to not query
        invalid_axons = [axon for axon in all_axons if axon not in valid_axons]

        bt.logging.trace(f"Axons to query: {valid_axons}")
        bt.logging.trace(f"Axons not to query: {invalid_axons}")

        valid_uids, invalid_uids = (
            [self.metagraph.hotkeys.index(axon.hotkey) for axon in valid_axons],
            [self.metagraph.hotkeys.index(axon.hotkey) for axon in invalid_axons],
        )

        bt.logging.debug(f"Valid UIDs to be queried: {valid_uids}")
        bt.logging.debug(f"Invalid UIDs not queried: {invalid_uids}")

        bt.logging.debug(f"Selecting UIDs for target group: {self.target_group}")

        # Determine how many axons must be included in one query group
        query_group_count = int(len(valid_axons) / self.max_targets) + (
            len(valid_axons) / self.max_targets % 1 > 0
        )
        targets_per_group = int(len(valid_axons) / query_group_count) + (
            len(valid_axons) / query_group_count % 1 > 0
        )

        if self.target_group == 0:
            # Determine start and end indices if target_group is zero
            start_index = 0
            end_index = targets_per_group
        else:
            # Determine start and end indices for non-zero target groups
            start_index = self.target_group * targets_per_group
            end_index = start_index + targets_per_group

        # Increment the target group
        if end_index >= len(valid_axons):
            end_index = len(valid_axons)
            self.target_group = 0
        else:
            self.target_group += 1

        bt.logging.debug(f"Start index: {start_index}, end index: {end_index}")

        if start_index == end_index:
            axons_to_query = valid_axons[start_index]
        else:
            # Determine the UIDs to query based on the start and end index
            axons_to_query = valid_axons[start_index:end_index]
            uids_to_query = [
                self.metagraph.hotkeys.index(axon.hotkey) for axon in axons_to_query
            ]

        return axons_to_query, uids_to_query, invalid_uids

    async def get_uids_to_query_async(self, all_axons):
        return await asyncio.to_thread(self.get_uids_to_query, all_axons)
