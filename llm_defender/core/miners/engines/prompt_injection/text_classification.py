"""
This module implements the base-engine used by the prompt-injection
feature of the llm-defender-subnet.
"""
import torch
from os import path
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
)
from transformers import pipeline
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

    """

    def __init__(
        self,
        prompt: str,
        engine_name: str = "Text Classification",
        prepare_only=False
    ):
        super().__init__(prompt, engine_name)

        if not prepare_only:
            self.engine_data = self.classification()

    def classification(self) -> list:
        """Perform text-classification for the prompt.

        This function performs classification of the given prompt to
        enable it to detect prompt injection. The function returns the
        label and score provided by the classifier and defines the class
        attributes based on the outcome of the classifier.

        Arguments:
            None

        Returns:
            data: An instance of dict containing the label and score
            received from the classifier.
        """

        tokenizer = AutoTokenizer.from_pretrained("laiyer/deberta-v3-base-prompt-injection", cache_dir=self.cache_dir)
        model = AutoModelForSequenceClassification.from_pretrained("laiyer/deberta-v3-base-prompt-injection", cache_dir=self.cache_dir)

        pipe = pipeline(
            "text-classification",
            model=model,
            tokenizer=tokenizer,
            truncation=True,
            max_length=512,
            device=torch.device("cuda" if torch.cuda.is_available() else "cpu"),
        )
        result = pipe(self.prompt)

        # Determine the confidence based on the score
        if result[0]["label"] == "SAFE":
            self.confidence = 1.0 - result[0]["score"]
        else:
            self.confidence = result[0]["score"]

        self.analyzed = True

        return [result[0]]

    def prepare(self) -> bool:
        """This function is used by prep.py
        
        The prep.py executes the prepare methods from all engines before
        the miner is launched. If you change the models used by the
        engines, you must also change this prepare function to match.
        """

        try:
            
            AutoTokenizer.from_pretrained("laiyer/deberta-v3-base-prompt-injection", cache_dir=self.cache_dir)
            AutoModelForSequenceClassification.from_pretrained("laiyer/deberta-v3-base-prompt-injection", cache_dir=self.cache_dir)
            
            return True
        except Exception as e:
            print(f'Error: {e}')
            return False

