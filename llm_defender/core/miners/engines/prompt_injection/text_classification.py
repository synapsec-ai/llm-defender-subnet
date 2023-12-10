"""
This module implements the base-engine used by the prompt-injection
feature of the llm-defender-subnet.
"""
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
)
from transformers import pipeline
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

    """

    def __init__(self, prompt: str = None, name: str = "engine:text_classification"):
        super().__init__(name=name)
        self.prompt = prompt

    def _calculate_confidence(self):
        # Determine the confidence based on the score
        if self.output["outcome"] != "UNKNOWN":
            if self.output["outcome"] == "SAFE":
                return 0.0
            else:
                return 1.0
        else:
            return 0.5

    def _populate_data(self, results):
        if results:
            return {"outcome": results[0]["label"], "score": results[0]["score"]}
        return {"outcome": "UNKNOWN"}

    def prepare(self):
        _, _ = self.initialize()

    def initialize(self):
        try:
            model = AutoModelForSequenceClassification.from_pretrained(
                "laiyer/deberta-v3-base-prompt-injection", cache_dir=self.cache_dir
            )

            tokenizer = AutoTokenizer.from_pretrained(
                "laiyer/deberta-v3-base-prompt-injection", cache_dir=self.cache_dir
            )
        except Exception as e:
            raise Exception(
                f"Error occurred when initializing model or tokenizer: {e}"
            ) from e

        if not model or not tokenizer:
            raise ValueError("Model or tokenizer is empty")

        return model, tokenizer

    def execute(self, model, tokenizer):
        """Perform text-classification for the prompt.

        This function performs classification of the given prompt to
        enable it to detect prompt injection. The function returns the
        label and score provided by the classifier and defines the class
        attributes based on the outcome of the classifier.

        Arguments:
            Model:
                The model used by the pipeline
            Tokenizer:
                The tokenizer used by the pipeline
        """

        if not model or not tokenizer:
            raise ValueError("Model or tokenizer is empty")
        try:
            pipe = pipeline(
                "text-classification",
                model=model,
                tokenizer=tokenizer,
                truncation=True,
                max_length=512,
                device=torch.device("cuda" if torch.cuda.is_available() else "cpu"),
            )
            results = pipe(self.prompt)
        except Exception as e:
            raise Exception(
                f"Error occurred during text classification pipeline execution: {e}"
            ) from e

        self.output = self._populate_data(results)
        self.confidence = self._calculate_confidence()

        bt.logging.debug(
            f"Text Classification engine executed (Confidence: {self.confidence} - Output: {self.output})"
        )
        return True
