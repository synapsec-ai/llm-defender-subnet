import typing
import bittensor as bt
import pydantic


class LLMDefenderProtocol(bt.Synapse):
    """
    This class implements the protocol definition for the the
    llm-defender subnet.

    The protocol is a simple request-response communication protocol in
    which the validator sends a request to the miner for processing
    activities.
    """

    # Parse variables
    output: typing.Optional[dict] = None

    synapse_uuid: str = pydantic.Field(
        ...,
        description="Synapse UUID provides an unique identifier for the prompt send out by the validator",
        allow_mutation=False
    )

    synapse_nonce: str = pydantic.Field(
        ...,
        description="Synapse nonce provides an unique identifier for the prompt send out by the validator",
        allow_mutation=False
    )

    synapse_timestamp: str = pydantic.Field(
        ...,
        description="Synapse timestamp provides an unique identifier for the prompt send out by the validator",
        allow_mutation=False
    )

    subnet_version: int = pydantic.Field(
        ...,
        description="Subnet version provides information about the subnet version the Synapse creator is running at",
        allow_mutation=False,
    )

    analyzer: str = pydantic.Field(
        ...,
        title="analyzer",
        description="The analyzer field provides instructions on which Analyzer to execute on the miner",
        allow_mutation=False,
    )

    synapse_signature: str = pydantic.Field(
        ...,
        title="synapse_signature",
        description="The synapse_signature field provides the miner means to validate the origin of the Synapse",
        allow_mutation=False,
    )

    def deserialize(self) -> bt.Synapse:
        """Deserialize the instance of the protocol"""
        return self
