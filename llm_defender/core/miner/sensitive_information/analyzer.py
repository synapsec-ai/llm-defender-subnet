import secrets
import time
from typing import List

import bittensor as bt

# Import custom modules
import llm_defender.base as LLMDefenderBase
import llm_defender.core.miner as LLMDefenderCore


class SensitiveInformationAnalyzer:
    """This class is responsible for handling the analysis for Sensitive Information

    The SensitiveInformationAnalyzer class contains all the code for a Miner neuron
    to generate a confidence score for a prompt containing sensitive information.

    Attributes:
        model:
            Stores the 'model' output for an engine.
        tokenizer:
            Stores the 'tokenizer' output for an engine.

    Methods:
        execute:
            Executes the engines within the analyzer

    """

    def __init__(
        self, wallet: bt.wallet, subnet_version: int, wandb_handler, miner_uid: str
    ):
        self.wallet = wallet
        self.miner_hotkey = self.wallet.hotkey.ss58_address
        self.subnet_version = subnet_version
        self.miner_uid = miner_uid

        self.model, self.tokenizer = (
            LLMDefenderCore.TokenClassificationEngine().initialize()
        )

        self.wandb_handler = wandb_handler
        if self.wandb_handler:
            self.wandb_enabled = True
        else:
            self.wandb_enabled = False

    def execute(self, synapse: LLMDefenderBase.SubnetProtocol, prompts: List[str], log_level):
        output = {
            "analyzer": "Sensitive Information",
            "confidence": None,
            "engines": [],
        }
        engine_confidences = []

        # Execute Token Classification engine
        token_classification_engine = LLMDefenderCore.TokenClassificationEngine(
            prompts=prompts
        )
        token_classification_engine.execute(model=self.model, tokenizer=self.tokenizer, log_level=log_level)
        token_classification_response = (
            token_classification_engine.get_response().get_dict()
        )
        output["engines"].append(token_classification_response)
        engine_confidences.append(token_classification_response["confidence"])

        # Calculate confidence score
        output["confidence"] = sum(engine_confidences) / len(engine_confidences)

        # Add subnet version and UUID to the output
        output["subnet_version"] = self.subnet_version
        output["synapse_uuid"] = synapse.synapse_uuid
        output["nonce"] = secrets.token_hex(24)
        output["timestamp"] = str(int(time.time()))

        data_to_sign = f'{output["synapse_uuid"]}{output["nonce"]}{self.wallet.hotkey.ss58_address}{output["timestamp"]}'

        # Generate signature for the response
        output["signature"] = LLMDefenderBase.sign_data(self.wallet.hotkey, data_to_sign)

        # Wandb logging
        if self.wandb_enabled:
            self.wandb_handler.set_timestamp()

            wandb_logs = [
                {
                    f"{self.miner_uid}:{self.miner_hotkey}_Token Classification Confidence": token_classification_response[
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

            LLMDefenderBase.utils.subnet_logger(
                severity="TRACE",
                message=f"Wandb logs added: {wandb_logs}",
                log_level=log_level
            )

        return output
