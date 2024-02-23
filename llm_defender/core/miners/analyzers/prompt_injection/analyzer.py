"""Analyzer method for the prompt injection analyzer"""
import time
import bittensor as bt
from llm_defender.base.protocol import LLMDefenderProtocol
from llm_defender.core.miners.analyzers.prompt_injection.yara import YaraEngine
from llm_defender.core.miners.analyzers.prompt_injection.text_classification import TextClassificationEngine
from llm_defender.core.miners.analyzers.prompt_injection.vector_search import VectorEngine
from llm_defender.base.utils import sign_data, wandb_available

if wandb_available():
    import wandb

class PromptInjectionAnalyzer:
    """This class is responsible for handling the analysis for prompt injection
    
    The PromptInjectionAnalyzer class contains all of the code for a Miner neuron
    to generate a confidence score for a Prompt Injection Attack.

    Attributes:
        chromadb_client:
            Stores the 'clint' output from VectorEngine.initialize() This is from:
            llm_defender/core/miners/engines/prompt_injection/vector_search.py
        model:
            Stores the 'model' output for an engine.
        tokenizer:
            Stores the 'tokenized' output for an engine.
        yara_rules:
            Stores the 'rules' output of YaraEngine.initialize() This is only when using
            the YaraEngine, located at:

            llm_defender/core/miners/engines/prompt_injection/yara.py

    Methods:
        execute:
            Executes the engines within the analyzer
    
    """

    def __init__(self, wallet: bt.wallet, subnet_version: int, args):
        # Parameters
        self.wallet = wallet
        self.subnet_version = subnet_version

        # Configuration options for the analyzer
        self.chromadb_client = VectorEngine().initialize()
        self.model, self.tokenizer = TextClassificationEngine().initialize()
        self.yara_rules = YaraEngine().initialize()

        # Wandb
        self.wandb_available = wandb_available()        

        if args.use_wandb == 'True':
            self.use_wandb = True
        else:
            self.use_wandb = False

        if self.use_wandb and self.wandb_available:
            self.wandb_project = args.wandb_project 
            self.wandb_entity = args.wandb_entity
    
    def execute(self, synapse: LLMDefenderProtocol) -> dict:
        # Responses are stored in a dict
        output = {"analyzer": "Prompt Injection", "prompt": synapse.prompt, "confidence": None, "engines": []}

        engine_confidences = []

        # Execute YARA engine
        yara_engine = YaraEngine(prompt=synapse.prompt)
        yara_engine.execute(rules=self.yara_rules)
        yara_response = yara_engine.get_response().get_dict()
        output["engines"].append(yara_response)
        engine_confidences.append(yara_response["confidence"])

        # Execute Text Classification engine
        text_classification_engine = TextClassificationEngine(prompt=synapse.prompt)
        text_classification_engine.execute(model=self.model, tokenizer=self.tokenizer)
        text_classification_response = text_classification_engine.get_response().get_dict()
        output["engines"].append(text_classification_response)
        engine_confidences.append(text_classification_response["confidence"])

        # Execute Vector Search engine
        vector_engine = VectorEngine(prompt=synapse.prompt)
        vector_engine.execute(client=self.chromadb_client)
        vector_response = vector_engine.get_response().get_dict()
        output["engines"].append(vector_response)
        engine_confidences.append(vector_response["confidence"])

        # Calculate confidence score
        output["confidence"] = sum(engine_confidences)/len(engine_confidences)

        # Add subnet version and UUID to the output
        output["subnet_version"] = self.subnet_version
        output["synapse_uuid"] = synapse.synapse_uuid

        # Generate signature for the response
        output["signature"] = sign_data(self.wallet, output["synapse_uuid"])

        # Wandb logging
        if self.use_wandb and self.wandb_available:
            try:
                wandb_logs = [
                    {"YARA Confidence":yara_response['confidence']},
                    {"Text Classification Confidence":text_classification_response['confidence']},
                    {"Vector Search Confidence":vector_response['confidence']},
                    {"Total Confidence":output['confidence']}
                ]   
                log_timestamp = int(time.time())
                for wl in wandb_logs:
                    wandb.log(wl, step=log_timestamp)    
                bt.logging.trace(f"Wandb logs added: {wandb_logs}")
            except:
                bt.logging.trace("Wandb logging failed for engine confidences.")
        
        synapse.output = output

        return output