"""
This module implements the base-engine used by the prompt-injection
feature of the llm-defender-subnet.
"""
from re import sub
from transformers import GPT2LMHeadModel, GPT2Tokenizer
import bittensor as bt
from os import path, makedirs

from llm_defender.base.engine import BaseEngine


class TextToSqlEngine(BaseEngine):
    """Text-to-SQL Engine

    This engine is used by the llm-defender-subnet miners for
    analyzing prompt-injection strings that have been formatted as SQL
    queries.

    The purpose is to identity potential prompt injections that can be
    modeled as SQL queries by using static analysis of the resulting SQL
    query.

    """

    def __init__(self, prompt: str = None, name: str = "engine:text-to-sql"):
        super().__init__(name=name)

        self.prompt = prompt
        self.keywords = {
            "CREATE": 1.0,
            "DELETE": 1.0,
            "DROP": 1.0,
            "INSERT": 1.0,
            "INTO": 1.0,
            "TRUNCATE": 1.0,
            "UPDATE": 1.0,
        }

        # Ensure the keywords are in lowercase
        self.keywords = {key.lower(): value for key, value in self.keywords.items()}

    def _calculate_confidence(self):
        """
        The standard implementation looks for a match in the list of
        keywords and if match is found, the output value of this
        function is set to the value. The highest value is kept and
        returned as float.

        In order to properly fine-tune the engine, you should also
        fine-tune the scoring algorithm.
        """

        if self.output["outcome"] == "converted":
            scores = [self.keywords.get(string, None) for string in self._clean()]

            return max((score for score in scores if score is not None), default=0.5)

        return 0.5

    def _populate_data(self, results):
        if results:
            return {
                "outcome": "converted",
                "data": f"{results[len(self.prompt) :].strip()}",
            }
        return {"outcome": "notConverted"}

    def prepare(self):
        # Check cache directory
        if not path.exists(self.cache_dir):
            try:
                makedirs(self.cache_dir)
            except OSError as e:
                raise OSError(f"Unable to create cache directory: {e}") from e

        _, _ = self.initialize()

        return True

    def initialize(self):
        try:
            model = GPT2LMHeadModel.from_pretrained(
                "rakeshkiriyath/gpt2Medium_text_to_sql"
            )
            tokenizer = GPT2Tokenizer.from_pretrained(
                "rakeshkiriyath/gpt2Medium_text_to_sql"
            )
        except Exception as e:
            raise Exception(f"Error occurred while initializing the models: {e}") from e

        return model, tokenizer

    def execute(self, model, tokenizer):
        input_tensor = tokenizer.encode(self.prompt, return_tensors="pt")

        output = model.generate(
            input_tensor,
            max_length=256,
            num_return_sequences=1,
            pad_token_id=tokenizer.eos_token_id,
        )

        decoded_output = tokenizer.decode(output[0], skip_special_tokens=True)

        self.output = self._populate_data(decoded_output)
        self.confidence = self._calculate_confidence()

        bt.logging.debug(
            f"Text-to-SQL engine executed (Confidence: {self.confidence} - Output: {self.output})"
        )
        return True

    def _clean(self) -> list:
        """
        This method returns a clean list of the prompt given as an
        argument for the class.
        """

        # Remove non-alphanumeric characters and extra whitespaces
        clean_prompt = sub(r"[^a-zA-Z0-9 ]", "", self.output["data"])
        clean_prompt = sub(r"\s+", " ", clean_prompt).strip()

        # Convert the individual words into lower-case and return them in a list to be
        # processed further.
        return [word.lower() for word in clean_prompt.split()]
