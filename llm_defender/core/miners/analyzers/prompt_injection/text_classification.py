"""
This module implements the base-engine used by the prompt-injection
feature of the llm-defender-subnet.
"""
import requests
import bittensor as bt
from llm_defender.base.engine import BaseEngine


class TextClassificationEngine(BaseEngine):
    """Text classification engine for detecting prompt injection.

    This class implements an engine that uses text classification to
    identity prompt injection attacks. The text classification engine is
    the primary detection method along with the heuristics engine
    detecting prompt injection attacks.

    Whereas the heuristics engine is a collection of specialized
    sub-engines the text-classification engine focuses on analyzing the
    prompt as a whole and thus has a potential to yield better results
    than the heuristic based approaches.

    Attributes:
        name (from the BaseEngine located at llm_defender/base/engine.py):
            A str instance displaying the name of the engine. 

    Methods:
        __init__():
            Defines the name and prompt attributes for the TextClassificationEngine 
            object.
        execute():
            This function sends request to classify the given prompt to
            enable it to detect prompt injection. The function returns the
            label and score provided by the classifier and defines the class
            attributes based on the outcome of the classifier.
    """

    def __init__(self, name: str = "prompt_injection:text_classification"):
        """
        Initializes the TextClassificationEngine object with the name and prompt attributes.

        Arguments:
            name:
                A str instance displaying the name of the engine. Default is
                'prompt_injection:text_classification'

        Returns:
            None
        """        
        super().__init__(name=name)

    def execute(self, prompt: str):
        """Perform text-classification for the prompt.

        This function performs classification of the given prompt to
        enable it to detect prompt injection. The function returns the
        label and score provided by the classifier and defines the class
        attributes based on the outcome of the classifier.

        Arguments:
            prompt:
                The prompt to be classified

        Raises:
            Exception:
                The Exception will be raised if a general error occurs during the 
                execution of the text classification request.
        """

        url = "http://3.255.228.124:8000/is-prompt-injection"
        body = {
            "prompt": prompt
        }
        response = requests.post(url, json=body)

        if response.status_code == 200:
            result = float(response.text)
        else:
            raise Exception(f"Text classification request failed. Status code: {response.status_code}")
        
        label = "SAFE" if result == 0 else "INJECTION"

        bt.logging.debug(
            f"Text Classification engine executed (Output: {result} - Label: {label})"
        )

        return {"outcome": label, "score": result}
