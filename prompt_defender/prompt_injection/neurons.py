"""Module for prompt-injection neurons for the
prompt-defender-subnet.

Long description

Typical example usage:

    foo = bar()
    foo.bar()
"""
from argparse import ArgumentParser
from typing import Tuple
from secrets import choice
import sys
import torch
import bittensor as bt
from datasets import load_dataset
from prompt_defender.base.neuron import BaseNeuron
from prompt_defender.prompt_injection.protocol import PromptInjectionProtocol
from prompt_defender.prompt_injection.miner.engines import (
    HeuristicsEngine,
    TextClassificationEngine,
)
from prompt_defender.base.common import EnginePrompt
from prompt_defender.base.common import normalize_list


class PromptInjectionMiner(BaseNeuron):
    """Summary of the class

    Class description

    Attributes:

    """

    def __init__(self, parser: ArgumentParser):
        super().__init__(parser=parser, profile="miner")

        self.neuron_config = self.config(
            bt_classes=[bt.subtensor, bt.logging, bt.wallet, bt.axon]
        )
        self.wallet, self.subtensor, self.metagraph, self.miner_uid = self.setup()

    def setup(self) -> Tuple[bt.wallet, bt.subtensor, bt.metagraph, str]:
        """This function setups the neuron.

        The setup function initializes the neuron by registering the
        configuration.

        Args:
            None

        Returns:
            wallet:
                An instance of bittensor.wallet containing information about
                the wallet
            subtensor:
                An instance of bittensor.subtensor doing ?
            metagraph:
                An instance of bittensor.metagraph doing ?
            miner_uid:
                An instance of str consisting of the miner UID

        Raises:
            AttributeError:
        """

        bt.logging(config=self.neuron_config, logging_dir=self.neuron_config.full_path)
        bt.logging.info(
            f"Initializing miner for subnet: {self.neuron_config.netuid} on network: {self.neuron_config.subtensor.chain_endpoint} with config:\n {self.neuron_config}"
        )

        # Setup the bittensor objects
        try:
            wallet = bt.wallet(config=self.neuron_config)
            subtensor = bt.subtensor(config=self.neuron_config)
            metagraph = subtensor.metagraph(self.neuron_config.netuid)
        except AttributeError as e:
            bt.logging.error(f"Unable to setup bittensor objects: {e}")
            sys.exit()

        bt.logging.info(
            f"Bittensor objects initialized:\nMetagraph: {metagraph}\
            \nSubtensor: {subtensor}\nWallet: {wallet}"
        )

        # Validate that our hotkey can be found from metagraph
        if wallet.hotkey.ss58_address not in metagraph.hotkeys:
            bt.logging.error(
                f"Your miner: {wallet} is not registered to chain connection: \
                {subtensor}. Run btcli register and try again"
            )
            sys.exit()

        # Get the unique identity (UID) from the network
        miner_uid = metagraph.hotkeys.index(wallet.hotkey.ss58_address)
        bt.logging.info(f"Miner is running with UID: {miner_uid}")

        return wallet, subtensor, metagraph, miner_uid

    def blacklist(self, synapse: PromptInjectionProtocol) -> Tuple[bool, str]:
        """
        This function is executed before the synapse data has been
        deserialized.

        On a practical level this means that whatever blacklisting
        operations we want to perform, it must be done based on the
        request headers or other data that can be retrieved outside of
        the request data.

        As it currently stats, we want to blacklist requests that are
        not originating from valid validators.

        This function must return [True, ""] for blacklisted requests
        and [False, ""] for non-blacklisted requests.
        """

        # Blacklist entities that have not registered their hotkey
        if synapse.dendrite.hotkey not in self.metagraph.hotkeys:
            bt.logging.info(f"Blacklisted unknown hotkey: {synapse.dendrite.hotkey}")
            return (
                True,
                f"Hotkey {synapse.dendrite.hotkey} was not found from metagraph.hotkeys",
            )

        # Blacklist entities that are not validators
        # uid = self.metagraph.hotkeys.index(synapse.dendrite.hotkey)
        # if not self.metagraph.validator_permit[uid]:
        #     bt.logging.info(f"Blacklisted unknown hotkey: {synapse.dendrite.hotkey}")
        #     return (True, f"Hotkey {synapse.dendrite.hotkey} is not a validator")

        # Allow all other entities
        bt.logging.info(f"Accepted hotkey: {synapse.dendrite.hotkey}")
        return (False, f"Accepted hotkey: {synapse.dendrite.hotkey}")

    def priority(self, synapse: PromptInjectionProtocol) -> float:
        """
        This function defines the priority based on which the validators
        are selected. Higher priority value means the input from the
        validator is processed faster.
        """

        # Prioritize validators based on their stake
        uid = self.metagraph.hotkeys.index(synapse.dendrite.hotkey)
        priority = float(self.metagraph.S[uid])

        bt.logging.info(
            f"Prioritized: {synapse.dendrite.hotkey} with value: {priority}"
        )

        return priority

    def forward(self, synapse: PromptInjectionProtocol) -> PromptInjectionProtocol:
        """The function is executed once the data from the
        validator has been deserialized, which means we can utilize the
        data to control the behavior of this function.
        """
        # Responses are stored in a list
        output = []

        # Initialize the engines and their weights to be used for the
        # detections. Initializing the engine also executes the engine.
        engines = [
            HeuristicsEngine(prompt=synapse.prompt),
            TextClassificationEngine(prompt=synapse.prompt),
        ]

        for engine in engines:
            output.append(engine.get_response())
        
        synapse.output = output

        return synapse


class PromptInjectionValidator(BaseNeuron):
    """Summary of the class

    Class description

    Attributes:

    """

    def __init__(self, parser: ArgumentParser):
        super().__init__(parser=parser, profile="validator")

        self.neuron_config = self.config(
            bt_classes=[bt.subtensor, bt.logging, bt.wallet]
        )
        (
            self.wallet,
            self.subtensor,
            self.dendrite,
            self.metagraph,
            self.scores,
        ) = self.setup()

    def setup(
        self,
    ) -> Tuple[bt.wallet, bt.subtensor, bt.dendrite, bt.metagraph, torch.Tensor]:
        """This function setups the neuron.

        The setup function initializes the neuron by registering the
        configuration.

        Args:
            None

        Returns:
            wallet:
                An instance of bittensor.wallet containing information about
                the wallet
            subtensor:
                An instance of bittensor.subtensor doing ?
            dendrite:
                An instance of bittensor.dendrite doing ?
            metagraph:
                An instance of bittensor.metagraph doing ?
            scores:
                An instance of torch.Tensor doing ?

        Raises:
            AttributeError:
        """
        bt.logging(config=self.neuron_config, logging_dir=self.neuron_config.full_path)
        bt.logging.info(
            f"Initializing validator for subnet: {self.neuron_config.netuid} on network: \
            {self.neuron_config.subtensor.chain_endpoint} with config:\n {self.neuron_config}"
        )

        # Setup the bittensor objects
        try:
            wallet = bt.wallet(config=self.neuron_config)
            subtensor = bt.subtensor(config=self.neuron_config)
            dendrite = bt.dendrite(wallet=wallet)
            metagraph = subtensor.metagraph(self.neuron_config.netuid)
        except AttributeError as e:
            bt.logging.error(f"Unable to setup bittensor objects: {e}")
            sys.exit()

        bt.logging.info(
            f"Bittensor objects initialized:\nMetagraph: {metagraph}\
            \nSubtensor: {subtensor}\nWallet: {wallet}"
        )

        # Validate that our hotkey can be found from metagraph
        if wallet.hotkey.ss58_address not in metagraph.hotkeys:
            bt.logging.error(
                f"Your validator: {wallet} is not registered to chain connection: \
                {subtensor}. Run btcli register and try again"
            )
            sys.exit()

        # Get the unique identity (UID) from the network
        validator_uid = metagraph.hotkeys.index(wallet.hotkey.ss58_address)
        bt.logging.info(f"Validator is running with UID: {validator_uid}")

        # Setup initial scoring weights
        scores = torch.zeros_like(metagraph.S, dtype=torch.float32)
        bt.logging.info(f"Validation weights have been initialized: {scores}")

        return wallet, subtensor, dendrite, metagraph, scores


    def process_responses(self, query: dict, responses: list):
        """
        This function processes the responses received from the miners.
        """

        for i, response in enumerate(responses):
            # Set the score for empty responses to 0
            if not response:
                self.scores[i] = (
                    self.neuron_config.alpha * self.scores[i]
                    + (1 - self.neuron_config.alpha) * 0.0
                )
                continue

            # Enumerate the responses from the Engines used by the miner
            # and extract properties used for the scoring function
            engine_scores = []
            miner_score = []
            for engine_response in response:

                if (
                    engine_response["analyzed"] is False
                    or engine_response["confidence"] < 0.0
                    or engine_response["confidence"] > 1.0
                    or (
                        query["data"]["isPromptInjection"] is False
                        and engine_response["confidence"] > 0.6
                    )
                    or (
                        query["data"]["isPromptInjection"] is True
                        and engine_response["confidence"] < 0.4
                    )
                ):
                    engine_scores.append(0.0)
                elif engine_response["confidence"] > 0.4 and engine_response["confidence"] < 0.6:
                    engine_scores.append(0.5)
                else:
                    engine_scores.append(1.0)


            miner_score = sum(engine_scores)

            bt.logging.info(f"Normalized scores: {miner_score}")

            bt.logging.info(f"Score before adjustment: {self.scores[i]}")
            self.scores[i] = (
                self.neuron_config.alpha * self.scores[i]
                + (1 - self.neuron_config.alpha) * miner_score
            )
            bt.logging.info(f"Score after adjustment: {self.scores[i]}")

    def penalty(self) -> bool:
        """
        Penalty function.
        """
        return False

    def serve_prompt(self) -> EnginePrompt:
        """Generates a prompt to serve to a miner

        This function selects a random prompt from the dataset to be
        served for the miners connected to the subnet.

        Args:
            None

        Returns:
            prompt: An instance of EnginePrompt
        """

        train_dataset = load_dataset("deepset/prompt-injections", split="train")

        entry = choice(train_dataset)

        prompt = EnginePrompt(
            engine="Prompt Injection",
            prompt=entry["text"],
            data={"isPromptInjection": entry["label"] == 1},
        )

        return prompt
