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
    VectorEngine
)
from prompt_defender.base.common import EnginePrompt


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

        # Otherwise prioritize validators based on their stake
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
        output = {
            "confidence": 0.5,
            "prompt": synapse.prompt,
            "engines": []
        }

        # Initialize the engines and their weights to be used for the
        # detections. Initializing the engine also executes the engine.
        engines = [
            HeuristicsEngine(prompt=synapse.prompt),
            TextClassificationEngine(prompt=synapse.prompt),
            VectorEngine(prompt=synapse.prompt, db_path="/tmp/chromadb/")
        ]

        engine_confidences = []
        for engine in engines:
            output["engines"].append(engine.get_response())
            engine_confidences.append(engine.confidence)

        if all(0.0 <= val <= 1.0 for val in engine_confidences):
            output["confidence"] = sum(engine_confidences) / len(engine_confidences)
        else:
            bt.logging.error(f'Confidence scores received from engines are out-of-bound: {engine_confidences}')
            sys.exit()
        
        synapse.output = output

        return synapse


class PromptInjectionValidator(BaseNeuron):
    """Summary of the class

    Class description

    Attributes:

    """

    def __init__(self, parser: ArgumentParser):
        super().__init__(parser=parser, profile="validator")

        self.max_engines = 3
        self.timeout = 60
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

        # Determine target value for scoring
        if query["data"]["isPromptInjection"] is True:
            target = 1.0
        else:
            target = 0.0

        bt.logging.debug(f"Target set to: {target}")

        for i, response in enumerate(responses):
            bt.logging.debug(f"Processing response {i} with content: {response}")
            # Set the score for empty responses to 0
            if not response.output:
                bt.logging.debug(f"Received an empty response: {response}")
                self.scores[i] = (
                    self.neuron_config.alpha * self.scores[i]
                    + (1 - self.neuron_config.alpha) * 0.0
                )
                continue

            response_time = response.dendrite.process_time
            response_score = self.calculate_score(
                response=response.output,
                target=target,
                response_time=response_time,
                hotkey=response.dendrite.hotkey,
            )

            bt.logging.info(f"Response score for the request: {response_score}")

            bt.logging.info(f"Score before adjustment: {self.scores[i]}")
            self.scores[i] = (
                self.neuron_config.alpha * self.scores[i]
                + (1 - self.neuron_config.alpha) * response_score
            )
            bt.logging.info(f"Score after adjustment: {self.scores[i]}")

    def calculate_score(
        self, response, target: float, response_time: float, hotkey: str
    ) -> float:
        """This function sets the score based on the response.

        Returns:
            score: An instance of float depicting the score for the
            response
        """

        # Calculate distances to target value for each engine and take the mean
        distances = [
            abs(target - confidence)
            for confidence in [engine["confidence"] for engine in response["engines"]]
        ]
        distance_score = (
            1 - sum(distances) / len(distances) if len(distances) > 0 else 1.0
        )

        # Calculate score for the speed of the response
        speed_score = 1.0 - (response_time / self.timeout)

        # Calculate score for the number of engines used
        engine_score = len(response) / self.max_engines

        # Validate individual scores
        if (
            not (0.0 <= distance_score <= 1.0)
            or not (0.0 <= speed_score <= 1.0)
            or not (0.0 <= engine_score <= 1.0)
        ):
            bt.logging.error(
                f"Calculated out-of-bounds individual scores:\nDistance: {distance_score}\nSpeed: {speed_score}\nEngine: {engine_score} for the response: {response} from hotkey: {hotkey}"
            )

            return 0.0

        # Determine final score
        distance_weight = 0.6
        speed_weight = 0.2
        num_engines_weight = 0.2

        bt.logging.debug(
            f"Scores: Distance: {distance_score}, Speed: {speed_score}, Engine: {engine_score}"
        )

        score = (
            distance_weight * distance_score
            + speed_weight * speed_score
            + num_engines_weight * engine_score
        )

        if score > 1.0 or score < 0.0:
            bt.logging.error(
                f"Calculated out-of-bounds score: {score} for the response: {response} from hotkey: {hotkey}"
            )

            return 0.0

        return score

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

        dataset = load_dataset("deepset/prompt-injections", split="test")

        entry = choice(dataset)

        prompt = EnginePrompt(
            engine="Prompt Injection",
            prompt=entry["text"],
            data={"isPromptInjection": entry["label"] == 1},
        )

        return prompt
