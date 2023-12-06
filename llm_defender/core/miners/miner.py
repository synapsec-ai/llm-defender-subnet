"""Module for prompt-injection neurons for the
llm-defender-subnet.

Long description

Typical example usage:

    foo = bar()
    foo.bar()
"""
from argparse import ArgumentParser
from typing import Tuple
import sys
import bittensor as bt
from llm_defender.base.neuron import BaseNeuron
from llm_defender.base.protocol import LLMDefenderProtocol
from llm_defender.core.miners.engines.prompt_injection import (
    heuristics,
    text_classification,
    vector_search,
)


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

        args = parser.parse_args()
        self.set_miner_weights = args.miner_set_weights

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
                f"Your miner: {wallet} is not registered to chain connection: {subtensor}. Run btcli register and try again"
            )
            sys.exit()

        # Get the unique identity (UID) from the network
        miner_uid = metagraph.hotkeys.index(wallet.hotkey.ss58_address)
        bt.logging.info(f"Miner is running with UID: {miner_uid}")

        return wallet, subtensor, metagraph, miner_uid

    def blacklist(self, synapse: LLMDefenderProtocol) -> Tuple[bool, str]:
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

    def priority(self, synapse: LLMDefenderProtocol) -> float:
        """
        This function defines the priority based on which the validators
        are selected. Higher priority value means the input from the
        validator is processed faster.
        """

        # Otherwise prioritize validators based on their stake
        uid = self.metagraph.hotkeys.index(synapse.dendrite.hotkey)
        priority = float(self.metagraph.S[uid])

        bt.logging.info(
            f"Prioritized: {synapse.dendrite.hotkey} with value: {priority}"
        )

        return priority

    def forward(self, synapse: LLMDefenderProtocol) -> LLMDefenderProtocol:
        """The function is executed once the data from the
        validator has been deserialized, which means we can utilize the
        data to control the behavior of this function.
        """
        # Responses are stored in a list
        output = {"confidence": 0.5, "prompt": synapse.prompt, "engines": []}

        # Initialize the engines and their weights to be used for the
        # detections. Initializing the engine also executes the engine.
        engines = [
            heuristics.HeuristicsEngine(prompt=synapse.prompt),
            text_classification.TextClassificationEngine(prompt=synapse.prompt),
            vector_search.VectorEngine(prompt=synapse.prompt, db_path="/tmp/chromadb/"),
        ]

        engine_confidences = []
        for engine in engines:
            output["engines"].append(engine.get_response())
            engine_confidences.append(engine.confidence)

        if all(0.0 <= val <= 1.0 for val in engine_confidences):
            output["confidence"] = sum(engine_confidences) / len(engine_confidences)
        else:
            bt.logging.error(
                f"Confidence scores received from engines are out-of-bound: {engine_confidences}, output: {output}"
            )
            sys.exit()

        # Nullify engines after execution
        engines = None

        synapse.output = output

        return synapse
