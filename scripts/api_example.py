"""API example to interact with the subnet miners.

This python script implements a simple API client that demonstrates how
external applications can utilize the subnet.

"""

import json
import bittensor as bt
import uuid
import secrets
import time
from llm_defender.base.protocol import LLMDefenderProtocol
from llm_defender.base.utils import sign_data
from llm_defender import __spec_version__ as subnet_version


class sampleAPIClient:
    """This class is a sample implementation on how the miners in the
    llm-defender subnet can be queried externally.

    The sample code must be adjusted accordingly to meet your exact
    use-case.

    Prerequisites:
    - Validator registered in the subnet with more than 20k staked TAO
    - Whitelisted validator
    """

    def __init__(self, wallet: bt.wallet, netuid: int, network: str):

        # Wallet is needed to sign message request and send out the synapse
        self.wallet = wallet

        # Netuid is used to determine which network to send the synapse to
        self.netuid = netuid

        # Subtensor and metagraph are required for the subnet
        # connectivity
        self.subtensor = bt.subtensor(network=network)
        self.metagraph = self.subtensor.metagraph(netuid=self.netuid)

    def _generate_signature(self):
        """This method generates the necessary information to validate
        the synapse sent out to the miners."""

        # Random UUID used to correlate miner and validator logs and to
        # identify the individual synapses
        synapse_uuid = str(uuid.uuid4())

        # Random nonce used to prevent replay attacks. Each nonce can be
        # used exactly once and must be unique for each synapse
        nonce = secrets.token_hex(24)

        # Current timestamp is used as a part of the signature
        # validation. The request is denied if the timestamp is too far
        # into the past/future
        timestamp = str(int(time.time()))

        # Data to be signed is a combination of synapse_uuid, nonce and timestamp
        data = f"{synapse_uuid}{nonce}{timestamp}"

        signature = sign_data(wallet=self.wallet, data=data)

        return synapse_uuid, nonce, timestamp, signature

    def get_axons(self):
        """This methods get the list of axons to send the Synapse to.

        Querying the Axons from the metagraph for each execution is
        slow. Instead, caching should be used to ensure the replies are
        received fast enough.
        """

        # Get all Axons from the subnet
        all_axons = self.metagraph.axons

        # TODO: Filter the axons based on your use-case

        return all_axons

    def query_axons(self, prompt, analyzer, axons):
        """This method sends out the synapse to the axons within the
        network and returns the responses"""

        # Get the signature fields
        synapse_uuid, nonce, timestamp, signature = self._generate_signature()

        # Dendrite is needed to send the query
        dendrite = bt.dendrite(wallet=self.wallet)
        
        # Send the query
        responses = dendrite.query(
            axons=axons,
            synapse=LLMDefenderProtocol(
                prompt=prompt,
                analyzer=analyzer,
                subnet_version=subnet_version,
                synapse_uuid=synapse_uuid,
                synapse_signature=signature,
                synapse_nonce=nonce,
                synapse_timestamp=timestamp
            ),
            timeout=6,
            deserialize=True
        )
    
        return responses

wallet = bt.wallet(name="validator", hotkey="default")

api_example = sampleAPIClient(wallet=wallet, netuid=38, network="test")

# Prompt is the input to be sent out to the miners (i.e., the string/data you want to be analyzed)
prompt = "What is the meaning of life?"

# Analyzer is the high-level category for the group of engines to
# execute (i.e., what do you want analyze).
analyzer = "Prompt Injection" # Currently only prompt injection is supported

# Miners to query
axons = api_example.get_axons()

# Collect responses
responses = api_example.query_axons(prompt, analyzer, axons)

# Print responses
for response in responses:
    if response.output:
        print(json.dumps(response.output, indent=2, default=str))
