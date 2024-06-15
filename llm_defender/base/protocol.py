from typing import List, Dict
import bittensor as bt
import pydantic


class MetricsProtocol(bt.Synapse):
    """This class implements the Synapse responsible for the
    feedback-loop back towards the miner after processing the response
    received from the miner"""

    # This variable contains the metrics to be sent back to the Miner
    response_object: Dict

    synapse_uuid: str = pydantic.Field(
        ...,
        description="Synapse UUID provides a unique identifier for the prompt sent out by the validator",
    )

    synapse_nonce: str = pydantic.Field(
        ...,
        description="Synapse nonce provides a unique identifier for the prompt sent out by the validator",
    )

    synapse_timestamp: str = pydantic.Field(
        ...,
        description="Synapse timestamp provides a unique identifier for the prompt sent out by the validator",
    )

    synapse_signature: str = pydantic.Field(
        ...,
        title="synapse_signature",
        description="The synapse_signature field provides the miner means to validate the origin of the Synapse",
    )


class SubnetProtocol(bt.Synapse):
    """
    This class implements the protocol definition for the the
    llm-defender subnet.

    The protocol is a simple request-response communication protocol in
    which the validator sends a request to the miner for processing
    activities.
    """

    # Parse variables
    output: dict | None = None

    synapse_uuid: str = pydantic.Field(
        ...,
        description="Synapse UUID provides a unique identifier for the prompt sent out by the validator",
    )

    synapse_nonce: str = pydantic.Field(
        ...,
        description="Synapse nonce provides a unique identifier for the prompt sent out by the validator",
    )

    synapse_timestamp: str = pydantic.Field(
        ...,
        description="Synapse timestamp provides a unique identifier for the prompt sent out by the validator",
    )

    subnet_version: int = pydantic.Field(
        ...,
        description="Subnet version provides information about the subnet version the Synapse creator is running at",
    )

    analyzer: str | None = pydantic.Field(
        None,
        title="analyzer",
        description="The analyzer field provides instructions on which Analyzer to execute on the miner",
    )

    synapse_signature: str = pydantic.Field(
        ...,
        title="synapse_signature",
        description="The synapse_signature field provides the miner means to validate the origin of the Synapse",
    )

    synapse_prompts: List[str] | None = pydantic.Field(
        None,
        title="synapse_prompt",
        description="Optional field providing additional prompt information.",
    )

    synapse_hash: str | None = pydantic.Field(
        None,
        title="synapse_hash",
        description="Optional field providing hash information for the synapse.",
    )

    def deserialize(self) -> bt.Synapse:
        """Deserialize the instance of the protocol"""
        return self
