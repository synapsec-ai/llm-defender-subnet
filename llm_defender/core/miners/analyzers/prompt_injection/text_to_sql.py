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

    Attributes:
        prompt:
            An instance of str displaying the prompt to analyze for SQL 
            query-formatted prompt injection attacks.
        name (from the BaseEngine located at llm_defender/base/engine.py):
            An instance of str displaying the name of the engine. This 
            attribute originally belongs to the BaseEngine class inehrited 
            by the TextToSqlEngine class.
        cache_dir (from the BaseEngine located at llm_defender/base/engine.py):
            The cache directory allocated for the engine. 
        keywords:
            An instance of dict displaying the SQL keywords (str) as keys, and the
            corresponding confidences (float) as the values associated with each
            key. 
        output:
            An instance of dict that must have the flag 'outcome'. The 'outcome' 
            value will be one of two strings--'converted' or 'notConverted'. If the
            'outcome' flag has the 'converted' value, the output dict will also contain
            the 'data' flag containing the output result data.
            
            Please reference the _populate_data() method for more details on how this
            output is generated.
        confidence:
            A float instance displaying the confidence score that a given prompt is a
            SQL query-based prompt injection attack. This value ranges from 0.0 to 1.0.

            Please reference the calculate_confidence() method for more details on how
            this value is generated.
        
    Methods:
        __init__():
            Defines the name, prompt, and keywords attributes.
        _calculate_confidence():
            Calculates a confidence score that self.prompt is a prompt-injection 
            string that has been formatted as an SQL query. 
            
            This value ranges from 0.0 to 1.0, with 0.5 being returned by default.
        _populate_data():
            Processes the results from the GPT2 model, and if valid, it formats and stores 
            the result data. The 'outcome' is set to either 'converted' or 'notConverted' 
            based on the presence of valid results.
        prepare():
            Checks and creates a cache directory if it doesn't exist, then calls 
            initialize() to set up the model and tokenizer.
        initialize():
            Loads the GPT-2 model and tokenizer from a pre-trained source.
        execute():
            Encodes self.prompt, generates GPT2 model output, decodes the output,
            populates the output attribute with self._populate_data(), and calculates 
            the confidence score with _calculate_confidence().
        _clean():
            This method returns a clean list of the prompt given as an argument for the class.
    """

    def __init__(self, prompt: str = None, name: str = "engine:text-to-sql"):
        """
        Initializes the TextToSqlEngine with attributes prompt, keywords and name.

        Arguments:
            prompt:
                An instance of str displaying the prompt to analyze for SQL 
                query-formatted prompt injection attacks.
            name:
                An instance of str displaying the name of the engine. Default is 
                'engine:text-to-sql'

        Returns:
            None
        """   
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

        Arguments:
            None

        Returns:
            The highest confidence value found by matching keywords.
            If none is found, the output defaults to a confidence score
            of 0.5.
        """

        if self.output["outcome"] == "converted":
            scores = [self.keywords.get(string, None) for string in self._clean()]

            return max((score for score in scores if score is not None), default=0.5)

        return 0.5

    def _populate_data(self, results):
        """
        Processes the results from the GPT2 model, and if valid, it formats and stores 
        the result data. 

        Arguments:
            results:
                The results from the GPT2 model.

        Returns:
            A dict instance with required flag 'outcome', set to either 'converted' 
            or 'notConverted' based on the presence of valid results. If the 'outcome' 
            flag has the associated value as 'converted', then the output will also 
            contain the flag 'data' with the converted results.
        """
        if results:
            return {
                "outcome": "converted",
                "data": f"{results[len(self.prompt) :].strip()}",
            }
        return {"outcome": "notConverted"}

    def prepare(self):
        """
        Prepares the TextToSqlEngine for analysis.

        Arguments:
            None

        Returns:
            True, if no errors are raised.

        Raises:
            OSError:
                The OSError is raised if a cache directory cannot be created.
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
        Initializes the GPT2 model & GPT2 tokenizer (GPT2LMHeadModel.from_pretrained()) 
        from a pre-trained source.

        Arguments:
            None
            
        Returns:
            model:
                The output of GPT2LMHeadModel.from_pretrained()
            tokenizer:
                The output of GPT2Tokenizer.from_pretrained()

        Raises:
            Exception:
                Raised if an error occurs while initializing the models.
        """
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
        """
        Encodes self.prompt, generates GPT2 model output, decodes the output,
        populates the output attribute with self._populate_data(), and populates 
        the confidence attribute with the _calculate_confidence() method.

        Arguments:
            model:
                The output of GPT2LMHeadModel.from_pretrained()
            tokenizer:
                The output of GPT2Tokenizer.from_pretrained()

        Returns:
            True
        """
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

        Arguments:
            None

        Returns:
            A list instance which displays all individual words in lower-case.
        """

        # Remove non-alphanumeric characters and extra whitespaces
        clean_prompt = sub(r"[^a-zA-Z0-9 ]", "", self.output["data"])
        clean_prompt = sub(r"\s+", " ", clean_prompt).strip()

        # Convert the individual words into lower-case and return them in a list to be
        # processed further.
        return [word.lower() for word in clean_prompt.split()]
