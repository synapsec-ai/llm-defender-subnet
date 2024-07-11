"""Module for prompt-injection neurons for the
llm-defender-subnet.

Long description

Typical example usage:

    foo = bar()
    foo.bar()
"""

from argparse import ArgumentParser
from collections import defaultdict
from typing import Tuple
import sys
import bittensor as bt

# Import custom modules
import llm_defender.base as LLMDefenderBase
import llm_defender.core.miner as LLMDefenderCore


class SubnetMiner(LLMDefenderBase.BaseNeuron):
    """SubnetMiner class for LLM Defender Subnet

    The SubnetMiner class contains all of the code for a Miner neuron

    Attributes:
        neuron_config:
            This attribute holds the configuration settings for the neuron:
            bt.subtensor, bt.wallet, bt.logging & bt.axon
        wallet:
            Represents an instance of bittensor.wallet returned from the setup() method.
        subtensor:
            An instance of bittensor.subtensor returned from the setup() method.
        metagraph:
            An instance of bittensor.metagraph returned from the setup() method.
        miner_uid:
            An int instance representing the unique identifier of the miner in the network returned
            from the setup() method.

    Methods:
        setup():
            This function initializes the neuron by registering the configuration.
        priority():
            This function defines the priority based on which the validators are
            selected. Higher priority value means the input from the validator is
            processed faster.
        feedback_forward():
            This function is executed when a metric synapse is received from a validator.
        analysis_forward():
            The function is executed once the data from the validator has been
            deserialized, which means we can utilize the data to control the behavior
            of this function.
        calculate_overall_confidence():
            This function calculates the overall confidence score for a prompt
            injection attack.
    """

    def __init__(self, parser: ArgumentParser):
        """
        Initializes the SubnetMiner class with attributes
        neuron_config, model, tokenizer, wallet, subtensor, metagraph,
        miner_uid

        Arguments:
            parser:
                An ArgumentParser instance.

        Returns:
            None
        """
        super().__init__(parser=parser, profile="miner")

        self.neuron_config = self.config(
            bt_classes=[bt.subtensor, bt.logging, bt.wallet, bt.axon]
        )

        # Read command line arguments and perform actions based on them
        args = parser.parse_args()
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


        self.validator_min_stake = args.validator_min_stake

        self.wallet, self.subtensor, self.metagraph, self.miner_uid = self.setup()

        # Initialize the analyzers
        self.analyzers = {
            str(
                LLMDefenderCore.SupportedAnalyzers.PROMPT_INJECTION
            ): LLMDefenderCore.PromptInjectionAnalyzer(
                wallet=self.wallet,
                subnet_version=self.subnet_version,
                wandb_handler=self.wandb_handler,
                miner_uid=self.miner_uid,
            ),
            str(
                LLMDefenderCore.SupportedAnalyzers.SENSITIVE_INFORMATION
            ): LLMDefenderCore.SensitiveInformationAnalyzer(
                wallet=self.wallet,
                subnet_version=self.subnet_version,
                wandb_handler=self.wandb_handler,
                miner_uid=self.miner_uid,
            ),
        }
        self.notification_synapses = defaultdict(
            lambda: {"synapse_uuid": None, "validator_hotkeys": []}
        )
        self.used_prompt_hashes = []
        self.validator_stats = {}

    def _update_validator_stats(self, hotkey, stat_type):
        """Helper function to update the validator stats"""
        if hotkey in self.validator_stats:
            if stat_type in self.validator_stats[hotkey]:
                self.validator_stats[hotkey][stat_type] += 1
            else:
                self.validator_stats[hotkey][stat_type] = 1
        else:
            self.validator_stats[hotkey] = {}
            self.validator_stats[hotkey][stat_type] = 1

    def _clean_prompt_hashes(self):
        """Truncates the local hash list to latest 100 prompts"""

        if self.used_prompt_hashes:

            self.neuron_logger(
                severity="DEBUG",
                message=f"Cleaning up local knowledge of used hashes. Old length: {len(self.used_prompt_hashes)}"
            )
            self.neuron_logger(
                severity="TRACE",
                message=f"First known hash before truncate: {self.used_prompt_hashes[0]}"
            )

            self.used_prompt_hashes = self.used_prompt_hashes[-100:]

            self.neuron_logger(
                severity="DEBUG",
                message="Cleaned up local knowledge of used hashes. New length: {len(self.used_prompt_hashes)}"
            )
            self.neuron_logger(
                severity="TRACE",
                message=f"First known hash after truncate: {self.used_prompt_hashes[0]}"
            )
        else:
            self.neuron_logger(
                severity="DEBUG",
                message=f"No hashes in local database to clean: {self.used_prompt_hashes}"
            )

    def clean_local_storage(self):
        """This method cleans the local miner storage"""

        self._clean_prompt_hashes()

    def setup(self) -> Tuple[bt.wallet, bt.subtensor, bt.metagraph, str]:
        """This function setups the neuron.

        The setup function initializes the neuron by registering the
        configuration.

        Arguments:
            None

        Returns:
            wallet:
                An instance of bittensor.wallet containing information about
                the wallet
            subtensor:
                An instance of bittensor.subtensor
            metagraph:
                An instance of bittensor.metagraph
            miner_uid:
                An instance of int consisting of the miner UID

        Raises:
            AttributeError:
                The AttributeError is raised if wallet, subtensor & metagraph cannot be logged.
        """
        bt.logging(config=self.neuron_config, logging_dir=self.neuron_config.full_path)
        self.neuron_logger(
            severity="INFO",
            message=f"Initializing miner for subnet: {self.neuron_config.netuid} on network: {self.neuron_config.subtensor.chain_endpoint} with config:\n {self.neuron_config}"
        )

        # Setup the bittensor objects
        try:
            wallet = bt.wallet(config=self.neuron_config)
            subtensor = bt.subtensor(config=self.neuron_config)
            metagraph = subtensor.metagraph(self.neuron_config.netuid)
        except AttributeError as e:
            self.neuron_logger(
                severity="ERROR",
                message=f"Unable to setup bittensor objects: {e}"
            )
            sys.exit()

        self.neuron_logger(
            severity="INFO",
            message=f"Bittensor objects initialized:\nMetagraph: {metagraph}\
            \nSubtensor: {subtensor}\nWallet: {wallet}"
        )

        # Validate that our hotkey can be found from metagraph
        if wallet.hotkey.ss58_address not in metagraph.hotkeys:
            self.neuron_logger(
                severity="ERROR",
                message=f"Your miner: {wallet} is not registered to chain connection: {subtensor}. Run btcli register and try again"
            )
            sys.exit()

        # Get the unique identity (UID) from the network
        miner_uid = metagraph.hotkeys.index(wallet.hotkey.ss58_address)
        self.neuron_logger(
            severity="INFO",
            message=f"Miner is running with UID: {miner_uid}"
        )

        return wallet, subtensor, metagraph, miner_uid

    def check_whitelist(self, hotkey):
        """
        Checks if a given validator hotkey has been whitelisted.

        Arguments:
            hotkey:
                A str instance depicting a hotkey.

        Returns:
            True:
                True is returned if the hotkey is whitelisted.
            False:
                False is returned if the hotkey is not whitelisted.
        """

        if isinstance(hotkey, bool) or not isinstance(hotkey, str):
            return False

        whitelisted_hotkeys = [
            "5G4gJgvAJCRS6ReaH9QxTCvXAuc4ho5fuobR7CMcHs4PRbbX",  # sn14 dev team test validator
        ]

        if hotkey in whitelisted_hotkeys:
            return True

        return False
    
    def blacklist_fn(self, synapse: LLMDefenderBase.SubnetProtocol | LLMDefenderBase.FeedbackProtocol) -> Tuple[bool, str]:
        """
        This function is executed before the synapse data has been
        deserialized.

        On a practical level this means that whatever blacklisting
        operations we want to perform, it must be done based on the
        request headers or other data that can be retrieved outside of
        the request data.

        As it currently stands, we want to blacklist requests that are
        not originating from valid validators. This includes:
        - unregistered hotkeys
        - entities which are not validators
        - entities with insufficient stake

        Returns:
            [True, ""] for blacklisted requests where the reason for
            blacklisting is contained in the quotes.
            [False, ""] for non-blacklisted requests, where the quotes
            contain a formatted string (f"Hotkey {synapse.dendrite.hotkey}
            has insufficient stake: {stake}",)
        """

        # Check whitelisted hotkeys (queries should always be allowed)
        if self.check_whitelist(hotkey=synapse.dendrite.hotkey):
            self.neuron_logger(
                severity="INFO",
                message=f"Accepted whitelisted hotkey: {synapse.dendrite.hotkey})"
            )
            return (False, f"Accepted whitelisted hotkey: {synapse.dendrite.hotkey}")

        # Blacklist entities that have not registered their hotkey
        if synapse.dendrite.hotkey not in self.metagraph.hotkeys:
            self.neuron_logger(
                severity="INFO",
                message=f"Blacklisted unknown hotkey: {synapse.dendrite.hotkey}"
            )
            return (
                True,
                f"Hotkey {synapse.dendrite.hotkey} was not found from metagraph.hotkeys",
            )

        # Blacklist entities that are not validators
        uid = self.metagraph.hotkeys.index(synapse.dendrite.hotkey)
        if not self.metagraph.validator_permit[uid]:
            self.neuron_logger(
                severity="INFO",
                message=f"Blacklisted non-validator: {synapse.dendrite.hotkey}"
            )
            return (True, f"Hotkey {synapse.dendrite.hotkey} is not a validator")

        # Blacklist entities that have insufficient stake
        stake = float(self.metagraph.S[uid])
        if stake < self.validator_min_stake:
            self.neuron_logger(
                severity="INFO",
                message=f"Blacklisted validator {synapse.dendrite.hotkey} with insufficient stake: {stake}"
            )
            return (
                True,
                f"Hotkey {synapse.dendrite.hotkey} has insufficient stake: {stake}",
            )

        # Allow all other entities
        self.neuron_logger(
            severity="INFO",
            message=f"Accepted hotkey: {synapse.dendrite.hotkey} (UID: {uid} - Stake: {stake})"
        )
        return (False, f"Accepted hotkey: {synapse.dendrite.hotkey}")
    
    def metric_blacklist(self, synapse: LLMDefenderBase.FeedbackProtocol) -> Tuple[bool, str]:
        """Wrapper for the blacklist function to avoid repetition in code"""
        return self.blacklist_fn(synapse=synapse)

    def analysis_blacklist(self, synapse: LLMDefenderBase.SubnetProtocol) -> Tuple[bool, str]:
        """Wrapper for the blacklist function to avoid repetition in code"""
        return self.blacklist_fn(synapse=synapse)

    def metric_priority(self, synapse: LLMDefenderBase.FeedbackProtocol) -> float:
        """Wrapper for the priority function to avoid repetition in code"""
        return self.priority_fn(synapse=synapse)

    def analysis_priority(self, synapse: LLMDefenderBase.SubnetProtocol) -> float:
        """Wrapper for the priority function to avoid repetition in code"""
        return self.priority_fn(synapse=synapse)

    def priority_fn(self, synapse: LLMDefenderBase.SubnetProtocol | LLMDefenderBase.FeedbackProtocol) -> float:
        """
        This function defines the priority based on which the validators
        are selected. Higher priority value means the input from the
        validator is processed faster.

        Inputs:
            synapse:
                The synapse should be theLLMDefender.SubnetProtocol class
                (from llm_defender/base/protocol.py)

        Returns:
            stake:
                A float instance of how much TAO is staked.
        """

        # Prioritize whitelisted validators
        if self.check_whitelist(hotkey=synapse.dendrite.hotkey):
            return 10000000.0

        # Otherwise prioritize validators based on their stake
        uid = self.metagraph.hotkeys.index(synapse.dendrite.hotkey)
        stake = float(self.metagraph.S[uid])

        self.neuron_logger(
            severity="DEBUG",
            message=f"Prioritized: {synapse.dendrite.hotkey} (UID: {uid} - Stake: {stake})"
        )

        return stake
    
    def feedback_forward(self, synapse: LLMDefenderBase.FeedbackProtocol) -> LLMDefenderBase.FeedbackProtocol:
        """Forward function that accepts the metrics synapse."""

        self.neuron_logger(
            severity="INFO",
            message=f'Received response object for the synapse_uuid: {synapse.synapse_uuid}. Response object: {synapse.response_object}'
        )

        # Miners should add custom code here if they want to collect or post-process the metrics.
        
        return synapse
    
    def analysis_forward(
        self, synapse: LLMDefenderBase.SubnetProtocol
    ) -> LLMDefenderBase.SubnetProtocol:
        """
        The function is executed once the data from the
        validator has been deserialized, which means we can utilize the
        data to control the behavior of this function. All confidence
        score outputs, alongside other relevant output metadata--subnet_version,
        synapse_uuid--are appended to synapse.output.

        Inputs:
            synapse:
                The synapse should be theLLMDefender.SubnetProtocol class
                (from llm_defender/base/protocol.py)

        Returns:
            synapse:
                The synapse should be theLLMDefender.SubnetProtocol class
                (from llm_defender/base/protocol.py)
        """

        is_notification_message = (
            synapse.synapse_prompts is None and synapse.synapse_hash is not None
        )

        # synapse_hash = synapse.synapse_hash
        hotkey = synapse.dendrite.hotkey
        # synapse_uuid = synapse.synapse_uuid

        # if is_notification_message:
            # If it's a notification synapse we can just ignore it
            # self.neuron_logger(severity="DEBUG",message="Received notification synapse. Ignoring.")
            # return synapse
        #     self.neuron_logger(severity="DEBUG",message=f"Processing notification synapse: {synapse}")
        #     self._update_validator_stats(hotkey, "received_notification_synapse_count")
        #     if synapse_hash in self.notification_synapses:
        #         self.notification_synapses[synapse_hash]["validator_hotkeys"].append(
        #             hotkey
        #         )
        #     else:
        #         self.notification_synapses[synapse_hash] = {
        #             "synapse_uuid": synapse_uuid,
        #             "validator_hotkeys": [hotkey],
        #         }

        #     self.neuron_logger(severity="SUCCESS",message=
        #         f"Processed notification synapse from hotkey: {hotkey} with UUID: {synapse.synapse_uuid} and hash: {synapse_hash}"
        #     )

        #     self._update_validator_stats(hotkey, "processed_notification_synapse_count")
        #     synapse.output = {"outcome": True}
        #     return synapse

        self._update_validator_stats(hotkey, "received_payload_synapse_count")

        # Print version information and perform version checks
        self.neuron_logger(
            severity="DEBUG",
            message=f"Synapse version: {synapse.subnet_version}, our version: {self.subnet_version}"
        )
        if synapse.subnet_version > self.subnet_version:
            self.neuron_logger(
                severity="WARNING",
                message=f"Received a synapse from a validator with higher subnet version ({synapse.subnet_version}) than yours ({self.subnet_version}). Please update the miner."
            )

        # Validate that nonce has not been reused
        if not self.validate_nonce(synapse.synapse_nonce):
            self.neuron_logger(
                severity="WARNING",
                message=f"Received a synapse with previous used nonce: {synapse}"
            )
            return synapse

        # Synapse signature verification
        data = f"{synapse.synapse_uuid}{synapse.synapse_nonce}{synapse.dendrite.hotkey}{synapse.synapse_timestamp}"
        if not LLMDefenderBase.validate_signature(
            hotkey=synapse.dendrite.hotkey,
            data=data,
            signature=synapse.synapse_signature,
        ):
            self.neuron_logger(
                severity="DEBUG",
                message=f"Failed to validate signature for the synapse. Hotkey: {synapse.dendrite.hotkey}, data: {data}, signature: {synapse.synapse_signature}"
            )
            return synapse
        self.neuron_logger(
            severity="DEBUG",
            message=f"Succesfully validated signature for the synapse. Hotkey: {synapse.dendrite.hotkey}, data: {data}, signature: {synapse.synapse_signature}"
        )

        if not (prompts := synapse.synapse_prompts):
            self.neuron_logger(
                severity="WARNING",
                message=f"Received a synapse without prompts: {synapse}"
            )
            return synapse

        # encoded_prompt = prompt.encode("utf-8")
        # prompt_hash = hashlib.sha256(encoded_prompt).hexdigest()

        # if (
        #     self.notification_synapses.get(prompt_hash) is None
        #     or self.notification_synapses[prompt_hash]["synapse_uuid"]
        #     != synapse.synapse_uuid
        # ):
        #     self.neuron_logger(severity="WARNING",message=
        #         f"Notification synapse not found from hotkey: {synapse.dendrite.hotkey}. UUID: {synapse.synapse_uuid} - SHA256: {prompt_hash}"
        #     )
        #     self.neuron_logger(severity="DEBUG",message=f"Notification synapses: {self.notification_synapses}")
        #     return synapse

        # if prompt_hash in self.used_prompt_hashes:
        #     self.neuron_logger(severity="WARNING",message=
        #         f"Received a prompt with recently used hash: {prompt_hash} originating from hotkey: {synapse.dendrite.hotkey}"
        #     )
        #     self.neuron_logger(severity="DEBUG",message=f"List of recent hashes: {self.used_prompt_hashes}")
        #     return synapse

        # validator_hotkey_to_reply = synapse.dendrite.hotkey
        # registered_hotkeys = self.notification_synapses[prompt_hash][
        #     "validator_hotkeys"
        # ]
        # if len(registered_hotkeys) > 1:
        #     self.neuron_logger(severity="WARNING",message=
        #         f"The same prompt: {prompt_hash} was sent by different validators: {registered_hotkeys}"
        #     )
        #     # Find the validator with the highest amount of stake
        #     duplicated_neurons = [
        #         neuron
        #         for neuron in self.metagraph.neurons
        #         if neuron.hotkey in registered_hotkeys
        #     ]
        #     max_stake_neuron = max(duplicated_neurons, key=lambda neuron: neuron.stake)
        #     validator_hotkey_to_reply = max_stake_neuron.hotkey

        # # If this validator doesn't have the highest amount fo stake, discard the message
        # if validator_hotkey_to_reply != synapse.dendrite.hotkey:
        #     self.neuron_logger(severity="WARNING",message=
        #         f"Discard message: {synapse} for validator: {synapse.dendrite.hotkey}, duplicated prompt"
        #     )
        #     return synapse

        # # Add to list of known hashes
        # self.used_prompt_hashes.append(prompt_hash)

        # Execute the correct analyzer
        if not LLMDefenderCore.SupportedAnalyzers.is_valid(synapse.analyzer):
            self.neuron_logger(
                severity="ERROR",
                message=f"Unable to process synapse: {synapse} due to invalid analyzer: {synapse.analyzer}"
            )
            return synapse

        self.neuron_logger(
            severity="DEBUG",
            message=f"Executing the {synapse.analyzer} analyzer"
        )
        output = self.analyzers[synapse.analyzer].execute(
            synapse=synapse, prompts=prompts, log_level=log_level
        )

        self.neuron_logger(
            severity="DEBUG",
            message=f"Setting synapse.output to: {output}"
        )
        synapse.output = output

        # Remove the message from the notification field
        # self.notification_synapses.pop(prompt_hash, None)
        self.neuron_logger(
            severity="DEBUG",
            message=f'Processed prompt "{prompts}" with analyzer: {output["analyzer"]}'
        )
        self.neuron_logger(
            severity="DEBUG",
            message=f'Engine data for {output["analyzer"]} analyzer: {output["engines"]}'
        )
        if self.check_whitelist(hotkey=synapse.dendrite.hotkey):
            self.neuron_logger(
                severity="SUCCESS",
                message=f'Processed payload synapse from whitelisted hotkey: {synapse.dendrite.hotkey} - Confidence: {output["confidence"]} - UUID: {output["synapse_uuid"]}'
            )
        else:
            self.neuron_logger(
                severity="SUCCESS",
                message=f'Processed payload synapse from UID: {self.metagraph.hotkeys.index(synapse.dendrite.hotkey)} - Confidence: {output["confidence"]} - UUID: {output["synapse_uuid"]}'
            )

        self._update_validator_stats(hotkey, "processed_payload_synapse_count")

        return synapse
