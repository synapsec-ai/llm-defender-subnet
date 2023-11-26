"""
This module implements the base-engine used by the prompt-injection
feature of the llm-defender-subnet.
"""
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
    ):
        super().__init__(prompt, engine_name)

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

        tokenizer = AutoTokenizer.from_pretrained("deepset/deberta-v3-base-injection")
        model = AutoModelForSequenceClassification.from_pretrained(
            "deepset/deberta-v3-base-injection",
            trust_remote_code=True,
            torch_dtype="auto",
        )

        pipe = pipeline("text-classification", model=model, tokenizer=tokenizer)
        result = pipe(self.prompt)

        # Determine the confidence based on the score
        if result[0]["label"] == "LEGIT":
            self.confidence = 1.0 - result[0]["score"]
        else:
            self.confidence = result[0]["score"]

        self.analyzed = True

        return [result[0]]
