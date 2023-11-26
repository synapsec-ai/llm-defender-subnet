"""Module for prompt-injection neurons for the
llm-defender-subnet.

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
from llm_defender.base.neuron import BaseNeuron
from llm_defender.base.utils import EnginePrompt


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
