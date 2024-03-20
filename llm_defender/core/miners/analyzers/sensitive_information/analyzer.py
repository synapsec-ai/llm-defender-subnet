import secrets
import time
import bittensor as bt
from llm_defender.base.protocol import LLMDefenderProtocol
from llm_defender.base.utils import sign_data
from llm_defender.core.miners.analyzers.sensitive_information.token_classification import TokenClassificationEngine
from llm_defender.core.miners.analyzers.sensitive_information.yara import YaraEngine

# Load wandb library only if it is enabled
from llm_defender import __wandb__ as wandb
if wandb is True:
    from llm_defender.base.wandb_handler import WandbHandler


class SensitiveInformationAnalyzer:
    """This class is responsible for handling the analysis for Sensitive Information

    The SensitiveInformationAnalyzer class contains all the code for a Miner neuron
    to generate a confidence score for a prompt containing sensitive information.

    Attributes:
        model:
            Stores the 'model' output for an engine.
        tokenizer:
            Stores the 'tokenizer' output for an engine.
        yara_rules:
            Stores the 'rules' output of YaraEngine.initialize() This is only when using
            the YaraEngine, located at:

            llm_defender/core/miners/engines/sensitive_information/yara.py

    Methods:
        execute:
            Executes the engines within the analyzer

    """

    def __init__(self, wallet: bt.wallet, subnet_version: int, wandb_handler, miner_uid: str):
        self.wallet = wallet
        self.miner_hotkey = self.wallet.hotkey.ss58_address
        self.subnet_version = subnet_version
        self.miner_uid = miner_uid

        self.model, self.tokenizer = TokenClassificationEngine().initialize()
        # self.yara_rules = YaraEngine().initialize()

        # Enable wandb if it has been configured
        if wandb is True:
            self.wandb_enabled = True
            self.wandb_handler = wandb_handler
        else:
            self.wandb_enabled = False
            self.wandb_handler = None

    def execute(self, synapse: LLMDefenderProtocol, prompt: str):
        output = {"analyzer": "Sensitive Information", "confidence": None, "engines": []}
        engine_confidences = []

        # Execute YARA engine
        # yara_engine = YaraEngine(prompt=prompt)
        # yara_engine.execute(rules=self.yara_rules)
        # yara_response = yara_engine.get_response().get_dict()
        # output["engines"].append(yara_response)
        # engine_confidences.append(yara_response["confidence"])

        # Execute Token Classification engine
        token_classification_engine = TokenClassificationEngine(prompt=prompt)
        token_classification_engine.execute(model=self.model, tokenizer=self.tokenizer)
        token_classification_response = token_classification_engine.get_response().get_dict()
        output["engines"].append(token_classification_response)
        engine_confidences.append(token_classification_response["confidence"])

        # Calculate confidence score
        output["confidence"] = sum(engine_confidences)/len(engine_confidences)

        # Add subnet version and UUID to the output
        output["subnet_version"] = self.subnet_version
        output["synapse_uuid"] = synapse.synapse_uuid
        output["nonce"] = secrets.token_hex(24)
        output["timestamp"] = str(int(time.time()))
        
        data_to_sign = f'{output["synapse_uuid"]}{output["nonce"]}{self.wallet.hotkey.ss58_address}{output["timestamp"]}'

        # Generate signature for the response
        output["signature"] = sign_data(self.wallet.hotkey, data_to_sign)

        # Wandb logging
        if self.wandb_enabled:
            self.wandb_handler.set_timestamp()

            wandb_logs = [
                # {f"{self.miner_uid}:{self.miner_hotkey}_YARA Confidence": yara_response['confidence']},
                {f"{self.miner_uid}:{self.miner_hotkey}_Token Classification Confidence": token_classification_response[
                    'confidence']},
                {f"{self.miner_uid}:{self.miner_hotkey}_Total Confidence": output['confidence']}
            ]

            for wandb_log in wandb_logs:
                self.wandb_handler.log(data=wandb_log)

            bt.logging.trace(f"Wandb logs added: {wandb_logs}")

        bt.logging.debug(f'Setting synapse.output to: {output}')
        synapse.output = output

        return output
