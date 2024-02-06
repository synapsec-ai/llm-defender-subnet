"""
This module implements the base-engine used by the prompt-injection
feature of the llm-defender-subnet.
"""
import torch
from os import path, makedirs
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
        prompt:
            A str instance displaying the prompt to be analyzed by the 
            TextClassificationEngine.
        name (from the BaseEngine located at llm_defender/base/engine.py):
            A str instance displaying the name of the engine. 
        cache_dir (from the BaseEngine located at llm_defender/base/engine.py):
            The cache directory allocated for the engine. 
        output:
            A dict instance with two flags--the 'outcome' flag is required and will 
            have a str instance for its value. The dict may also contain the flag 'score'
            if the model was able to come to a conclusion about the confidence score.
            
            Please reference the _populate_data() method for more details on how this
            output is generated.
        confidence:
            A float instance displaying the confidence score that a given prompt is a
            prompt attack for an LLM. This value ranges from 0.0 to 1.0.

            Please reference the _calculate_confidence() method for more details on how
            this value is generated.

    Methods:
        __init__():
            Defines the name and prompt attributes for the TextClassificationEngine 
            object.
        _calculate_confidence():
            Determines the confidence score for a given prompt being malicious & 
            returns the value which ranges from 0.0 (SAFE) to 1.0 (MALICIOUS).
        _populate_data():
            Returns a dict instance that displays the outputs for the 
            TextClassificationEngine.
        prepare():
            Checks and creates a cache directory if it doesn't exist, then 
            calls initialize() to set up the model and tokenizer.
        initialize():
            Loads the model and tokenizer used for the TextClassificationEngine.
        execute():
            This function performs classification of the given prompt to
            enable it to detect prompt injection. The function returns the
            label and score provided by the classifier and defines the class
            attributes based on the outcome of the classifier.
    """

    def __init__(self, prompt: str = None, name: str = "engine:text_classification"):
        """
        Initializes the TextClassificationEngine object with the name and prompt attributes.

        Arguments:
            prompt:
                A str instance displaying the prompt to be analyzed by the 
                TextClassificationEngine.
            name:
                A str instance displaying the name of the engine. Default is
                'engine:text_classification'

        Returns:
            None
        """        
        super().__init__(name=name)
        self.prompt = prompt

    def _calculate_confidence(self):
        """
        Determines a confidence value based on the self.output attribute. This
        value will be 0.0 if the 'outcome' flag in self.output is 'SAFE', 0.5 if 
        the flag value is 'UNKNOWN', and 1.0 otherwise.

        Arguments:
            None

        Returns:
            A float instance representing the confidence score, which is either 
            0.0, 0.5 or 1.0 depending on the state of the 'outcome' flag in the
            output attribute.
        """
        # Determine the confidence based on the score
        if self.output["outcome"] != "UNKNOWN":
            if self.output["outcome"] == "SAFE":
                return 0.0
            else:
                return 1.0
        else:
            return 0.5

    def _populate_data(self, results):
        """
        Takes in the results from the text classification and outputs a properly
        formatted dict instance which can later be used to generate a confidence 
        score with the _calculate_confidence() method.
        
        Arguments:
            results:
                A list instance depicting the results from the text classification 
                pipeline. The first element in the list (index=0) must be a dict
                instance contaning the flag 'outcome', and possibly the flag 'score'.

        Returns:
            A dict instance with two flags--the 'outcome' flag is required and will 
            have a str instance for its value. The dict may also contain the flag 'score'
            if the model was able to come to a conclusion about the confidence score.

            This dict instance is later saved to the output attribute.
        """
        if results:
            return {"outcome": results[0]["label"], "score": results[0]["score"]}
        return {"outcome": "UNKNOWN"}

    def prepare(self) -> bool:
        """
        Checks if the cache directory specified by the cache_dir attribute exists,
        and makes the directory if it does not. It then runs the initialize() method.
        
        Arguments:
            None

        Returns:
            True, unless OSError is raised in which case None will be returned.

        Raises:
            OSError:
                The OSError is raised if a cache directory cannot be created from 
                the self.cache_dir attribute.
        """
        # Check cache directory
        if not path.exists(self.cache_dir):
            try:
                makedirs(self.cache_dir)
            except OSError as e:
                raise OSError(f"Unable to create cache directory: {e}") from e
            
        _, _ = self.initialize()

        return True

    def initialize(self):
        """
        Initializes the model and tokenizer for the TextClassificationEngine.

        Arguments:
            None

        Returns:
            tuple:
                A tuple instance. The elements of the tuple are, in order:
                    model:
                        The model for the TextClassificationEngine.
                    tokenizer:
                        The tokenizer for the TextClassificationEngine.

        Raises:
            Exception:
                The Exception is raised if there was a general error when initializing 
                the model or tokenizer. This is conducted with try/except syntax.
            ValueError:
                The ValueError is raised if the model or tokenizer is empty.
        """
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

        Raises:
            ValueError:
                The ValueError is raised if the model or tokenizer arguments are 
                empty when the function is called.
            Exception:
                The Exception will be raised if a general error occurs during the 
                execution of the text classification pipeline. This is based on 
                try/except syntax.
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
