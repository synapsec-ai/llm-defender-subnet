"""Analyzer method for the prompt injection analyzer"""

import time
import secrets
from typing import List

import bittensor as bt

import llm_defender as LLMDefender


class PromptInjectionAnalyzer:
    """This class is responsible for handling the analysis for prompt injection

    The PromptInjectionAnalyzer class contains all the code for a Miner neuron
    to generate a confidence score for a Prompt Injection Attack.

    Attributes:
        model:
            Stores the 'model' output for an engine.
        tokenizer:
            Stores the 'tokenized' output for an engine.

    Methods:
        execute:
            Executes the engines within the analyzer

    """

    def __init__(
        self, wallet: bt.wallet, subnet_version: int, wandb_handler, miner_uid: str
    ):
        # Parameters
        self.wallet = wallet
        self.miner_hotkey = self.wallet.hotkey.ss58_address
        self.subnet_version = subnet_version
        self.miner_uid = miner_uid

        # Configuration options for the analyzer
        self.model, self.tokenizer = LLMDefender.TextClassificationEngine().initialize()

        self.wandb_handler = wandb_handler
        if self.wandb_handler:
            self.wandb_enabled = True
        else:
            self.wandb_enabled = False

    def execute(
        self, synapse: LLMDefender.SubnetProtocol, prompts: List[str]
    ) -> dict:
        # Responses are stored in a dict
        output = {"analyzer": "Prompt Injection", "confidence": None, "engines": []}

        # Execute Text Classification engine
        text_classification_engine = LLMDefender.TextClassificationEngine(
            prompts=prompts
        )
        text_classification_engine.execute(model=self.model, tokenizer=self.tokenizer)
        text_classification_response = (
            text_classification_engine.get_response().get_dict()
        )
        output["engines"].append(text_classification_response)

        # Calculate confidence score
        output["confidence"] = text_classification_response["confidence"]

        # Add subnet version and UUID to the output
        output["subnet_version"] = self.subnet_version
        output["synapse_uuid"] = synapse.synapse_uuid
        output["nonce"] = secrets.token_hex(24)
        output["timestamp"] = str(int(time.time()))

        data_to_sign = f'{output["synapse_uuid"]}{output["nonce"]}{self.wallet.hotkey.ss58_address}{output["timestamp"]}'

        # Generate signature for the response
        output["signature"] = LLMDefender.sign_data(self.wallet.hotkey, data_to_sign)

        # Wandb logging
        if self.wandb_enabled:
            self.wandb_handler.set_timestamp()

            wandb_logs = [
                {
                    f"{self.miner_uid}:{self.miner_hotkey}_Text Classification Confidence": text_classification_response[
                        "confidence"
                    ]
                },
                {
                    f"{self.miner_uid}:{self.miner_hotkey}_Total Confidence": output[
                        "confidence"
                    ]
                },
            ]

            for wandb_log in wandb_logs:
                self.wandb_handler.log(data=wandb_log)

            bt.logging.trace(f"Wandb logs added: {wandb_logs}")

        return output
