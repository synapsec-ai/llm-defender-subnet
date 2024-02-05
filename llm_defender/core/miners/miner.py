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
import requests
import bittensor as bt
from llm_defender.base.neuron import BaseNeuron
from llm_defender.base.protocol import LLMDefenderProtocol
from llm_defender.core.miners.engines.prompt_injection.yara import YaraEngine
from llm_defender.core.miners.engines.prompt_injection.text_classification import TextClassificationEngine
from llm_defender.core.miners.engines.prompt_injection.vector_search import VectorEngine
from llm_defender.base.utils import validate_miner_blacklist, wandb_available

if wandb_available():
    import wandb

class PromptInjectionMiner(BaseNeuron):
    """PromptInjectionMiner class for LLM Defender Subnet

    The PromptInjectionMiner class contains all of the code for a Miner neuron 
    to generate a confidence score for a Prompt Injection Attack.

    Attributes:
        neuron_config: 
            This attribute holds the configuration settings for the neuron: 
            bt.subtensor, bt.wallet, bt.logging & bt.axon
        miner_set_weights: 
            A boolean attribute that determines whether the miner sets weights. 
            This is set based on the command-line argument args.miner_set_weights.
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
        wallet: 
            Represents an instance of bittensor.wallet returned from the setup() method.
        subtensor: 
            An instance of bittensor.subtensor returned from the setup() method.
        metagraph: 
            An instance of bittensor.metagraph returned from the setup() method.
        miner_uid: 
            An int instance representing the unique identifier of the miner in the network returned 
            from the setup() method.
        hotkey_blacklisted: 
            A boolean flag indicating whether the miner's hotkey is blacklisted. It is initially 
            set to False and may be updated by the check_remote_blacklist() method.
        
    Methods:
        setup():
            This function initializes the neuron by registering the configuration.
        blacklist():
            This method blacklist requests that are not originating from valid 
            validators--insufficient hotkeys, entities which are not validators & 
            entities with insufficient stake 
        priority():
            This function defines the priority based on which the validators are 
            selected. Higher priority value means the input from the validator is 
            processed faster.
        forward():
            The function is executed once the data from the validator has been 
            deserialized, which means we can utilize the data to control the behavior 
            of this function.
        calculate_overall_confidence():
            This function calculates the overall confidence score for a prompt 
            injection attack.
        check_remote_blacklist():
            This function retrieves the remote blacklist (from the url: 
            https://ujetecvbvi.execute-api.eu-west-1.amazonaws.com/default/sn14-blacklist-api)
    """

    def __init__(self, parser: ArgumentParser):
        """
        Initializes the PromptInjectionMiner class with attributes neuron_config,
        miner_set_weights, chromadb_client, model, tokenizer, yara_rules, wallet,
        subtensor, metagraph, miner_uid & hotkey_blacklisted.

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

        args = parser.parse_args()
        if args.miner_set_weights == "False":
            self.miner_set_weights = False
        else:
            self.miner_set_weights = True
        
        self.validator_min_stake = args.validator_min_stake

        self.use_wandb = args.use_wandb
        if args.use_wandb and wandb_available():
            self.wandb_project = args.wandb_project 
            self.wandb_entity = args.wandb_entity

        self.chromadb_client = VectorEngine().initialize()

        self.model, self.tokenizer = TextClassificationEngine().initialize()
        self.yara_rules = YaraEngine().initialize()

        self.wallet, self.subtensor, self.metagraph, self.miner_uid = self.setup()

        self.hotkey_blacklisted = False

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
            "5G4gJgvAJCRS6ReaH9QxTCvXAuc4ho5fuobR7CMcHs4PRbbX", # sn14 dev team test validator
        ]

        if hotkey in whitelisted_hotkeys:
            return True

        return False

    def blacklist(self, synapse: LLMDefenderProtocol) -> Tuple[bool, str]:
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
            bt.logging.info(
                f"Accepted whitelisted hotkey: {synapse.dendrite.hotkey})"
            )
            return (False, f"Accepted whitelisted hotkey: {synapse.dendrite.hotkey}")

        # Blacklist entities that have not registered their hotkey
        if synapse.dendrite.hotkey not in self.metagraph.hotkeys:
            bt.logging.info(f"Blacklisted unknown hotkey: {synapse.dendrite.hotkey}")
            return (
                True,
                f"Hotkey {synapse.dendrite.hotkey} was not found from metagraph.hotkeys",
            )

        # Blacklist entities that are not validators
        uid = self.metagraph.hotkeys.index(synapse.dendrite.hotkey)
        if not self.metagraph.validator_permit[uid]:
            bt.logging.info(f"Blacklisted non-validator: {synapse.dendrite.hotkey}")
            return (True, f"Hotkey {synapse.dendrite.hotkey} is not a validator")

        # Blacklist entities that have insufficient stake
        stake = float(self.metagraph.S[uid])
        if stake <= self.validator_min_stake:
            bt.logging.info(
                f"Blacklisted validator {synapse.dendrite.hotkey} with insufficient stake: {stake}"
            )
            return (
                True,
                f"Hotkey {synapse.dendrite.hotkey} has insufficient stake: {stake}",
            )

        # Allow all other entities
        bt.logging.info(
            f"Accepted hotkey: {synapse.dendrite.hotkey} (UID: {uid} - Stake: {stake})"
        )
        return (False, f"Accepted hotkey: {synapse.dendrite.hotkey}")

    def priority(self, synapse: LLMDefenderProtocol) -> float:
        """
        This function defines the priority based on which the validators
        are selected. Higher priority value means the input from the
        validator is processed faster.

        Inputs:
            synapse:
                The synapse should be the LLMDefenderProtocol class 
                (from llm_defender/base/protocol.py)

        Returns:
            stake:
                A float instance of how much TAO is staked.
        """
        # Otherwise prioritize validators based on their stake
        uid = self.metagraph.hotkeys.index(synapse.dendrite.hotkey)
        stake = float(self.metagraph.S[uid])

        bt.logging.debug(
            f"Prioritized: {synapse.dendrite.hotkey} (UID: {uid} - Stake: {stake})"
        )

        return stake

    def forward(self, synapse: LLMDefenderProtocol) -> LLMDefenderProtocol:
        """
        The function is executed once the data from the
        validator has been deserialized, which means we can utilize the
        data to control the behavior of this function. All confidence 
        score outputs, alongside other relevant output metadata--subnet_version, 
        synapse_uuid--are appended to synapse.output.

        Inputs:
            synapse:
                The synapse should be the LLMDefenderProtocol class 
                (from llm_defender/base/protocol.py)

        Returns:
            synapse:
                The synapse should be the LLMDefenderProtocol class 
                (from llm_defender/base/protocol.py)
        """
        if synapse.subnet_version:
            bt.logging.debug(
                f"Synapse version: {synapse.subnet_version}, our version: {self.subnet_version}"
            )   
            if synapse.subnet_version > self.subnet_version:
                bt.logging.warning(
                    f"Received a synapse from a validator with higher subnet version ({synapse.subnet_version}) than yours ({self.subnet_version}). Please update the miner."
                )

        # Responses are stored in a list
        output = {"confidence": 0.5, "prompt": synapse.prompt, "engines": []}

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

        # Determine engine weights. These should corresponding to the
        # order of execution. You should modify these values as a part
        # of the fine-tuning process. Defaults to equal weight to all engines.
        engine_weights = [1/len(engine_confidences) for _ in engine_confidences]

        # Calculate confidence score
        output["confidence"] = self.calculate_overall_confidence(engine_confidences, engine_weights)

        # Add subnet version to the output
        if self.subnet_version:
            output["subnet_version"] = self.subnet_version
        else:
            output["subnet_version"] = None

        # Add synapse UUID to the output
        bt.logging.debug(f'Synapse: {synapse}')
        if synapse.synapse_uuid:
            output["synapse_uuid"] = synapse.synapse_uuid
        else:
            output["synapse_uuid"] = None

        synapse.output = output

        bt.logging.debug(f'Processed prompt: {output["prompt"]}')
        bt.logging.debug(f'Engine data: {output["engines"]}')
        bt.logging.success(f'Processed synapse from UID: {self.metagraph.hotkeys.index(synapse.dendrite.hotkey)} - Confidence: {output["confidence"]} - UUID: {output["synapse_uuid"]}')

        if self.use_wandb and wandb_available():
            wandb_logs = [
                {"YARA Confidence":yara_response['confidence']},
                {"Text Classification Confidence":text_classification_response['confidence']},
                {"Vector Search Confidence":vector_response['confidence']}
            ]            
            for wl in wandb_logs:
                wandb.log(wl, step=self.step)    
        
        return synapse
    
    def calculate_overall_confidence(self, confidences, weights):
        """
        Function to calculate the overall confidence
        
        Arguments:
            confidences:
                A list containing confidence values (between 0.0 and 1.0)
            weights:
                A list containing the weights for each associated confidence value 
                (the sum of all weights should approximate 1.0 with a tolerance of 0.01)

        Returns:
            overall_score:
                A float instance of the overall confidence score given confidences
                & weights

        Raises:
            ValueError:
                The ValueError is raised if
                    - The number of confidences & weights do not match
                    - The confidences are not between 0.0 and 1.0
                    - The sum of the weights does not approximate 1.0 (with a tolerance of 0.01)
        """
        if len(confidences) != len(weights):
            raise ValueError("Number of confidences and weights should match")
        
        if any(confidence < 0.0 or confidence > 1.0 for confidence in confidences):
            raise ValueError("Confidences should be between 0.0 and 1.0")
        
        if not (0.99 <= sum(weights) <= 1.01):
            raise ValueError("Sum of weights should be approximately 1.0")

        # Calculate the weighted average of confidences
        weighted_sum = sum(confidence * weight for confidence, weight in zip(confidences, weights))
        
        # Calculate the overall confidence
        overall_score = min(1.0, max(0.0, weighted_sum))
        bt.logging.debug(f'Calculated weighted confidence: {weighted_sum}. Original confidence: {sum(confidences)/len(confidences)}')

        if wandb_available() and self.use_wandb:
            wandb_logs = [
                {"Overall Confidence":overall_score},
                {"Weighted Confidence":weighted_sum},
                {"Original Confidence":sum(confidences)/len(confidences)}
            ]
            for wl in wandb_logs:
                wandb.log(wl, step=self.step)

        return overall_score

    def check_remote_blacklist(self):
        """
        Retrieves the remote blacklist & updates the hotkey_blacklisted 
        attribute.
        
        Arguments:
            None
        
        Returns:
            None

        Raises:
            requests.exceptions.JSONDecodeError:
                requests.exceptions.JSONDecodeError is raised if the response 
                could not be read from the blacklist API.
            requests.exceptions.ConnectionError:
                requests.exceptions.ConnectionError is raised if the function is 
                unable to connect to the blacklist API.
        """

        blacklist_api_url = "https://ujetecvbvi.execute-api.eu-west-1.amazonaws.com/default/sn14-blacklist-api"

        try:
            res = requests.get(url=blacklist_api_url, timeout=12)
            if res.status_code == 200:
                miner_blacklist = res.json()
                if validate_miner_blacklist(miner_blacklist):
                    bt.logging.trace(
                        f"Loaded remote miner blacklist: {miner_blacklist}"
                    )

                    is_blacklisted = False
                    for blacklist_entry in miner_blacklist:
                        if blacklist_entry["hotkey"] == self.wallet.hotkey.ss58_address:
                            bt.logging.warning(f'Your hotkey has been blacklisted. Reason: {blacklist_entry["reason"]}')
                            is_blacklisted = True
                    
                    self.hotkey_blacklisted = is_blacklisted
                        
                    
                bt.logging.trace(
                    f"Remote miner blacklist was formatted incorrectly or was empty: {miner_blacklist}"
                )

            else:
                bt.logging.warning(
                    f"Miner blacklist API returned unexpected status code: {res.status_code}"
                )

        except requests.exceptions.JSONDecodeError as e:
            bt.logging.error(f"Unable to read the response from the API: {e}")
        except requests.exceptions.ConnectionError as e:
            bt.logging.error(f"Unable to connect to the blacklist API: {e}")
