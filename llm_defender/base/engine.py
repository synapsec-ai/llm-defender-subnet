"""
This module implements the base-engine used by the prompt-injection
feature of the llm-defender-subnet.
"""
from llm_defender.base.utils import EngineResponse
from os import path


class BaseEngine:
    """
    This class implements the baseline engine used by specialized
    sub-engines to enable the detection capabilities for various
    prompt-injection attacks.

    The actual logic on how to handle a specific attack scenario should
    be implemented in child classes that inherit this parent class.
    """

    def __init__(self, prompt: str, engine_name: str):
        self.prompt = prompt
        self.confidence = 0.5
        self.analyzed = False
        self.engine_data = []
        self.engine_name = engine_name
        self.cache_dir = f"{path.expanduser('~')}/.llm-defender-subnet/cache"

    def get_response(self) -> EngineResponse:
        """
        This method creates a valid response based on the instance
        definition. Once all of the engines are executed, the responses
        are passed on to the subnet validator to be scored and weighted
        based on the response contents.
        """

        self.confidence = self._trim_value(self.confidence)

        response = EngineResponse(
            name=self.engine_name,
            confidence=self.confidence,
            engine_data=self.engine_data,
        )

        return response

    def _trim_value(self, value) -> float:
        """Trims the value to a valid range.

        This function trims the input variables such that is falls
        between [0, 1] as required by the validator.
        """

        if value < 0.0:
            return 0.0

        if value > 1.0:
            return 1.0

        return value
