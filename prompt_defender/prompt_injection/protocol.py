import bittensor as bt
import typing
import pydantic

class PromptInjectionProtocol(bt.Synapse):
    """
    This class implements the protocol definition for the the
    prompt-defender subnet.

    The protocol is a simple request-response communication protocol in
    which the validator sends a request to the miner for processing
    activities.
    """

    # Parse variables
    prompt: typing.Optional[str] = None
    engine: typing.Optional[str] = None
    output: typing.Optional[dict] = None

    roles: typing.List[str] = pydantic.Field(
        ...,
        title="Roles",
        description="An immutable list depicting the role",
        allow_mutation=False,
        regex=r'^(internal|external)$'
    )

    def deserialize(self) -> bt.Synapse:
        """Deserialize the instance of the protocol"""
        return self
    