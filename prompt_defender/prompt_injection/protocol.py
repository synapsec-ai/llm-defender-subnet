import bittensor as bt
import typing

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
    output: typing.Optional[list] = None

    def deserialize(self) -> list:
        """
        Something
        """
        return self.output
