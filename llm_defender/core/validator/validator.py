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
from datetime import datetime
from os import path, rename
import secrets
import time
import bittensor as bt
import numpy as np
import datasets
from collections import defaultdict 
import logging

# Import custom modules
import llm_defender.base as LLMDefenderBase
import llm_defender.core.validator as LLMDefenderCore


class SuppressPydanticFrozenFieldFilter(logging.Filter):
    def filter(self, record):
        return 'Ignoring error when setting attribute: 1 validation error for SubnetProtocol' not in record.getMessage()

class SubnetValidator(LLMDefenderBase.BaseNeuron):
    """Summary of the class

    Class description

    Attributes:

    """

    def __init__(self, parser: ArgumentParser):
        super().__init__(parser=parser, profile="validator")
        
        self.timeout = 18
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
        self.max_targets = 64
        self.target_group = None
        self.load_validator_state = None
        self.prompt = None
        self.query = None
        self.debug_mode = True
        self.prompt_api = None
        self.prompt_generation_disabled = True
        self.log_level = None

    def apply_config(self, bt_classes) -> bool:
        """This method applies the configuration to specified bittensor classes"""
        try:
            self.neuron_config = self.config(bt_classes=bt_classes)
        except AttributeError as e:
            self.neuron_logger(
                severity="ERROR",
                message=f"Unable to apply validator configuration: {e}"
            )
            raise AttributeError from e
        except OSError as e:
            self.neuron_logger(
                severity="ERROR",
                message=f"Unable to create logging directory: {e}"
            )
            raise OSError from e

        return True

    def validator_validation(self, metagraph, wallet, subtensor) -> bool:
        """This method validates the validator has registered correctly"""
        if wallet.hotkey.ss58_address not in metagraph.hotkeys:
            self.neuron_logger(
                severity="ERROR",
                message=f"Your validator: {wallet} is not registered to chain connection: {subtensor}. Run btcli register and try again"
            )
            return False

        return True

    def setup_bittensor_objects(self, neuron_config):
        """Setups the bittensor objects"""
        try:
            wallet = bt.wallet(config=neuron_config)
            subtensor = bt.subtensor(config=neuron_config)
            dendrite = bt.dendrite(wallet=wallet)
            metagraph = subtensor.metagraph(neuron_config.netuid)
        except AttributeError as e:
            self.neuron_logger(
                severity="ERROR",
                message=f"Unable to setup bittensor objects: {e}"
            )
            raise AttributeError from e

        self.hotkeys = copy.deepcopy(metagraph.hotkeys)

        self.wallet = wallet
        self.subtensor = subtensor
        self.dendrite = dendrite
        self.metagraph = metagraph

        return self.wallet, self.subtensor, self.dendrite, self.metagraph

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
        self.log_level = args.log_level

        # Setup logging
        bt.logging(config=self.neuron_config, logging_dir=self.neuron_config.full_path)
        if args.log_level in ("DEBUG", "DEBUGX"):
            bt.logging.enable_debug()
        elif args.log_level in ("TRACE", "TRACEX"):
            bt.logging.enable_trace()
        else:
            bt.logging.enable_default()
        
        # Enable healthcheck API if it is to be enabled
        if not args.disable_healthcheck:
            self.healthcheck_api = LLMDefenderBase.HealthCheckAPI(
                host=args.healthcheck_host, port=args.healthcheck_port
            )

            # Run healthcheck API
            self.healthcheck_api.run()

        # Suppress specific validation errors from pydantic
        bt.logging._logger.addFilter(SuppressPydanticFrozenFieldFilter())
        
        self.neuron_logger(
            severity="INFO",
            message=f"Initializing validator for subnet: {self.neuron_config.netuid} on network: {self.neuron_config.subtensor.chain_endpoint} with config: {self.neuron_config}"
        )
    


        # Setup the bittensor objects
        self.setup_bittensor_objects(self.neuron_config)

        self.neuron_logger(
            severity="INFO",
            message=f"Bittensor objects initialized:\nMetagraph: {self.metagraph}\nSubtensor: {self.subtensor}\nWallet: {self.wallet}"
        )

        if not args.debug_mode:
            # Validate that the validator has registered to the metagraph correctly
            if not self.validator_validation(self.metagraph, self.wallet, self.subtensor):
                raise IndexError("Unable to find validator key from metagraph")

            # Get the unique identity (UID) from the network
            validator_uid = self.metagraph.hotkeys.index(self.wallet.hotkey.ss58_address)
            self.neuron_logger(
                severity="INFO",
                message=f"Validator is running with UID: {validator_uid}"
            )

            # Disable debug mode
            self.debug_mode = False

            # Enable prompt generation
            self.prompt_generation_disabled = False

        
        if args.load_state == "False":
            self.load_validator_state = False
        else:
            self.load_validator_state = True

        if self.load_validator_state:
            self.load_state()
            self.load_miner_state()
        else:
            self.init_default_scores()
        
        self.target_group = 0

        # Setup prompt generation
        self.prompt_api = LLMDefenderCore.PromptGenerator(prompt_generation_disabled=self.prompt_generation_disabled, base_url=args.vllm_base_url, api_key=args.vllm_api_key, model=args.vllm_model_name)

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
            LLMDefenderBase.FeedbackProtocol(
                response_object=response_object,
                synapse_uuid=synapse_uuid,
                synapse_nonce=nonce,
                synapse_timestamp=timestamp,
                synapse_signature=LLMDefenderBase.sign_data(
                    hotkey=self.wallet.hotkey, data=data_to_sign, log_level=self.log_level
                ),
            ),
            timeout=2,
            deserialize=False
        )

        self.neuron_logger(
            severity="DEBUG",
            message=f'Metrics synapse processed for UUID: {synapse_uuid} and UID: {target_uid}'
        )

    def _parse_args(self, parser):
        return parser.parse_args()

    def process_responses(
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
            self.neuron_logger(
                severity="TRACE",
                message=f"Adding wandb logs for target: {target}"
            )

        self.neuron_logger(
            severity="DEBUG",
            message=f"Confidence target set to: {target}"
        )

        # Initiate the response objects
        response_data = []
        responses_invalid_uids = []
        responses_valid_uids = []

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
                        log_level=self.log_level,
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
                        log_level=self.log_level,
                    )
                )
            else:
                self.neuron_logger(
                    severity="ERROR",
                    message=f"Received unsupported analyzer: {query}"
                )
                raise AttributeError(f"Received unsupported analyzer: {query}")

            # Handle response
            response_data.append(response_object)

        self.neuron_logger(
            severity="INFO",
            message=f"Received valid responses from UIDs: {responses_valid_uids}"
        )
        self.neuron_logger(
            severity="INFO",
            message=f"Received invalid responses from UIDs: {responses_invalid_uids}"
        )

        # Add metrics
        self.healthcheck_api.append_metric(
            metric_name = "responses.total_valid_responses",
            value = len(responses_valid_uids)
        )
        
        self.healthcheck_api.append_metric(
            metric_name = "responses.total_invalid_responses",
            value = len(responses_invalid_uids)
        )
        
        return response_data, responses_invalid_uids, responses_valid_uids
    

    def determine_overall_scores(
        self, specialization_bonus_n=5
    ):

        top_prompt_injection_uids = np.argsort(self.prompt_injection_scores)[-specialization_bonus_n:][::-1]
        self.neuron_logger(
            severity="TRACE",
            message=f"Top {specialization_bonus_n} Miner UIDs for the Prompt Injection Analyzer: {top_prompt_injection_uids}"
        )
        top_sensitive_information_uids = np.argsort(self.sensitive_information_scores)[-specialization_bonus_n:][::-1]
        self.neuron_logger(
            severity="TRACE",
            message=f"Top {specialization_bonus_n} Miner UIDs for the Sensitive Information Analyzer: {top_sensitive_information_uids}"
        )

        for uid, _ in enumerate(self.hotkeys):

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

        self.neuron_logger(
            severity="TRACE",
            message=f"Calculated miner scores: {self.scores}"
        )

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

    def get_api_prompt(self, analyzer: str) -> dict:
        """Retrieves a prompt from the prompt API"""

        try:
            # get prompt
            prompt = self.prompt_api.construct(analyzer=analyzer, log_level=self.log_level)
            
            # check to make sure prompt is valid
            if LLMDefenderBase.validate_validator_api_prompt_output(prompt, self.log_level):
                self.neuron_logger(
                    severity="TRACEX",
                    message=f'Validated prompt: {prompt}'
                )
                return prompt
            self.neuron_logger(
                severity="INFOX",
                message=f'Failed to validate prompt: {prompt}'
            )
            return {}
        except Exception as e:
            self.neuron_logger(
                severity="ERROR",
                message=f"Failed to get prompt from prompt API: {e}"
            )

        return {}

    def get_prompt_from_dataset(self, analyzer: str) -> dict:
        """Fetches prompt from the dataset as a fallback to the prompt generation"""
        
        # Randomly choose which dataset to use
        if analyzer == "Prompt Injection":
            dataset = datasets.load_dataset("synapsecai/synthetic-prompt-injections")
        elif analyzer == "Sensitive Information":
            dataset = datasets.load_dataset("synapsecai/synthetic-sensitive-information")
        
        # Use prompts from the test dataset
        test_dataset = dataset["test"]

        # Shuffle the dataset and select random sample
        shuffled_dataset = test_dataset.shuffle()
        dataset_entry = shuffled_dataset.select(range(1))

        prompt = {
            "analyzer": analyzer,
            "category": dataset_entry["category"][0],
            "prompt": dataset_entry["text"][0],
            "label": dataset_entry["label"][0],
            "weight": 0.1, # Prompts from dataset should be given low weight in the scoring
        }

        self.neuron_logger(
            severity="INFO",
            message=f'Fetched prompt from the dataset: {prompt}'
        )
        return prompt


    def serve_prompt(self, analyzer: str) -> dict:
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

        # Load prompt from the prompt API
        entry = self.get_api_prompt(analyzer=analyzer)

        # Fallback to dataset if prompt loading from the API failed
        if not entry:
            entry = self.get_prompt_from_dataset(analyzer=analyzer)
        
        self.prompt = entry

        return self.prompt

    def check_hotkeys(self):
        """Checks if some hotkeys have been replaced in the metagraph"""
        if np.size(self.hotkeys) > 0:
            # Check if known state len matches with current metagraph hotkey length
            if len(self.hotkeys) == len(self.metagraph.hotkeys):
                current_hotkeys = self.metagraph.hotkeys
                for i, hotkey in enumerate(current_hotkeys):
                    if self.hotkeys[i] != hotkey:
                        self.neuron_logger(
                            severity="DEBUG",
                            message=f"Index '{i}' has mismatching hotkey. Old hotkey: '{self.hotkeys[i]}', new hotkey: '{hotkey}. Resetting score to 0.0"
                        )
                        self.neuron_logger(
                            severity="DEBUG",
                            message=f"Score before reset: {self.scores[i]}, Prompt Injeciton scores before reset: {self.prompt_injection_scores}, Sensitive Information scores before reset: {self.sensitive_information_scores}"
                        )
                        self.scores[i] = 0.0
                        self.prompt_injection_scores[i] = 0.0
                        self.sensitive_information_scores[i] = 0.0
                        self.miner_responses[self.hotkeys[i]] = []
                        self.neuron_logger(
                            severity="DEBUG",
                            message=f"Score after reset: {self.scores[i]}, Prompt Injeciton scores after reset: {self.prompt_injection_scores}, Sensitive Information scores after reset: {self.sensitive_information_scores}"
                        )
            else:
                # Init default scores
                self.neuron_logger(
                    severity="INFO",
                    message=f"Init default scores because of state and metagraph hotkey length mismatch. Expected: {len(self.metagraph.hotkeys)} had: {len(self.hotkeys)}"
                )
                self.init_default_scores()

            self.hotkeys = copy.deepcopy(self.metagraph.hotkeys)
        else:
            self.hotkeys = copy.deepcopy(self.metagraph.hotkeys)
    
    async def send_payload_message(self,
        synapse_uuid, uids_to_query, prompt_to_analyze, timeout
    ):
        # Broadcast query to valid Axons
        nonce = secrets.token_hex(24)
        timestamp = str(int(time.time()))
        data_to_sign = (
            f"{synapse_uuid}{nonce}{self.wallet.hotkey.ss58_address}{timestamp}"
        )
        self.neuron_logger(
            severity="DEBUG",
            message=f"Sent payload synapse to: {uids_to_query} with prompt: {prompt_to_analyze}."
        )
        prompts = [prompt_to_analyze["prompt"]]
        responses = await self.dendrite.forward(
            uids_to_query,
            LLMDefenderBase.SubnetProtocol(
                analyzer=prompt_to_analyze["analyzer"],
                subnet_version=self.subnet_version,
                synapse_uuid=synapse_uuid,
                synapse_signature=LLMDefenderBase.sign_data(
                    hotkey=self.wallet.hotkey, data=data_to_sign, log_level=self.log_level
                ),
                synapse_nonce=nonce,
                synapse_timestamp=timestamp,
                synapse_prompts=prompts,
            ),
            timeout=timeout,
            deserialize=True,
        )
        return responses

    def save_miner_state(self):
        """Saves the miner state to a file."""
        with open(
            f"{self.cache_path}/miners.pickle", "wb"
        ) as pickle_file:
            pickle.dump(self.miner_responses, pickle_file)

        filename = f"{self.cache_path}/miners.pickle"
        self.neuron_logger(
            severity="INFOX",
            message=f"Saved miner states to file: {filename}"
        )

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

                self.neuron_logger(
                    severity="DEBUG",
                    message="Loaded miner state from a file"
                )
            except Exception as e:
                self.neuron_logger(
                    severity="ERROR",
                    message=f"Miner response data reset because a failure to read the miner response data, error: {e}"
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
        self.neuron_logger(
            severity="INFO",
            message="Saving validator state."
        )

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
        self.neuron_logger(
            severity="INFOX",
            message=f"Saved the following state to file: {filename} step: {self.step}, scores: {self.scores}, prompt_injection_scores: {self.prompt_injection_scores}, sensitive_information_scores: {self.sensitive_information_scores}, hotkeys: {self.hotkeys}, last_updated_block: {self.last_updated_block}"
        )

    def init_default_scores(self) -> None:
        """Validators without previous validation knowledge should start
        with default score of 0.0 for each UID. The method can also be
        used to reset the scores in case of an internal error"""

        self.neuron_logger(
            severity="INFO",
            message="Initiating validator with default Prompt Injection Analyzer scores for each UID"
        )
        self.prompt_injection_scores = np.zeros_like(self.metagraph.S, dtype=np.float32)
        self.neuron_logger(
            severity="INFO",
            message=f"Prompt Injection Analyzer weights for validation have been initialized: {self.prompt_injection_scores}"
        )

        self.neuron_logger(
            severity="INFO",
            message="Initiating validator with default Sensiive Information Analyzer scores for each UID"
        )
        self.sensitive_information_scores = np.zeros_like(self.metagraph.S, dtype=np.float32)
        self.neuron_logger(
            severity="INFO",
            message=f"Sensitive Information Analyzer weights for validation have been initialized: {self.sensitive_information_scores}"
        )

        self.neuron_logger(
            severity="INFO",
            message="Initiating validator with default overall scores for each UID"
            )
        self.scores = np.zeros_like(self.metagraph.S, dtype=np.float32)
        self.neuron_logger(
            severity="INFO",
            message=f"Overall weights for validation have been initialized: {self.scores}"
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
                self.neuron_logger(
                    severity="INFO",
                    message="Loading validator state."
                )
                state = np.load(state_path)
                self.neuron_logger(
                    severity="INFOX",
                    message=f"Loaded the following state from file: {state}"
                )
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
                self.neuron_logger(
                    severity="INFOX",
                    message=f"Scores loaded from saved file: {self.scores}"
                )
            except Exception as e:
                self.neuron_logger(
                    severity="ERROR",
                    message=f"Validator state reset because an exception occurred: {e}"
                )
                self.reset_validator_state(state_path=state_path)
        else:
            self.init_default_scores()

    @LLMDefenderBase.timeout_decorator(timeout=30)
    async def sync_metagraph(self, metagraph, subtensor):
        """Syncs the metagraph"""

        self.neuron_logger(
            severity="INFOX",
            message=f"Syncing metagraph: {self.metagraph} with subtensor: {self.subtensor}"
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
        
        def get_weights_list(weights):

            max_value = 65535

            # Find the maximum value in the array
            original_max = np.max(weights)

            # Scale the array so the highest value becomes max_value
            if original_max == 0:
                scaled_array = weights
            else:
                scaled_array = (weights / original_max) * max_value

            # Round the scaled values to the nearest integer
            rounded_array = np.round(scaled_array).astype(int)

            # Convert the rounded array to a list
            preprocessed_result_list = rounded_array.tolist()
            result_list = []

            for result in preprocessed_result_list:
                if result == 0:
                    result_list.append(1)
                else:
                    result_list.append(result)

            if all(x == 1 for x in result_list):
                return [(x/max_value) for x in result_list]
            else:
                return [(x/max(result_list)) for x in result_list]

        if np.all(self.scores == 0.0):
            power_weights = self.scores 
        else:
            power_weights = power_scaling(self.scores)

        weights = get_weights_list(power_weights)
        
        self.neuron_logger(
            severity="INFO",
            message=f"Setting weights: {weights}"
        )
        if not self.debug_mode:
            self.neuron_logger(
                severity="DEBUGX",
                message=f"Setting weights with the following parameters: netuid={self.neuron_config.netuid}, wallet={self.wallet}, uids={self.metagraph.uids}, weights={weights}, version_key={self.subnet_version}"
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
                self.neuron_logger(
                    severity="SUCCESS",
                    message="Successfully set weights."
                )
            else:
                self.neuron_logger(
                    severity="ERROR",
                    message="Failed to set weights."
                )
        else:
            self.neuron_logger(
                severity="INFO",
                message=f"Skipped setting weights due to debug mode"
            )

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

        self.neuron_logger(
            severity="TRACEX",
            message=f"Filtered out axons. Original list: {len(axons)}, filtered list: {len(filtered_axons)}"
        )

        return filtered_axons

    def get_uids_to_query(self, all_axons) -> list:
        """Returns the list of UIDs to query"""

        # Filter Axons with invalid IPs
        valid_axons = self.determine_valid_axons(all_axons)

        # Determine list of Axons to not query
        invalid_axons = [axon for axon in all_axons if axon not in valid_axons]

        self.neuron_logger(
            severity="TRACEX",
            message=f"Axons to query: {valid_axons}"
        )
        self.neuron_logger(
            severity="TRACEX",
            message=f"Axons not to query: {invalid_axons}"
        )

        valid_uids, invalid_uids = (
            [self.metagraph.hotkeys.index(axon.hotkey) for axon in valid_axons],
            [self.metagraph.hotkeys.index(axon.hotkey) for axon in invalid_axons],
        )

        self.neuron_logger(
            severity="INFOX",
            message=f"Valid UIDs to be queried: {valid_uids}"
        )
        self.neuron_logger(
            severity="INFOX",
            message=f"Invalid UIDs not queried: {invalid_uids}"
        )

        self.neuron_logger(
            severity="DEBUG",
            message=f"Selecting UIDs for target group: {self.target_group}"
        )

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

        self.neuron_logger(
            severity="INFOX",
            message=f"Start index: {start_index}, end index: {end_index}"
        )

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
