"""This module implements the YARA engine for the llm-defender-subnet"""

from os import path, makedirs
from glob import glob
import bittensor as bt
import yara
from llm_defender.base.engine import BaseEngine


class YaraEngine(BaseEngine):
    """This class implements the YARA engine.
    
    YARA is a powerful pattern matching tool that can be used to analyze
    strings based on boolean operators and other logical patterns. As a
    part of prompt injection analyzer, the YARA engine is used to detect
    well known prompt injections and other patterns within the inputs
    that could be an indication of prompt injections.

    The detection logic is described within the rules and in order to
    fine-tune this engine, you should add additional rules within the
    yara_rules directory.
    
    """
    def __init__(self, prompt: str=None, name: str = "engine:yara"):
        super().__init__(name=name)

        self.prompt = prompt
        self.compiled = f"{self.cache_dir}/compiled_rules"
        self.rules = f"{path.dirname(__file__)}/yara_rules/*.yar"

    def _calculate_confidence(self):
        if self.output["outcome"] != "NoRuleMatch":
            match_accuracies = []
            for match in self.output["meta"]:
                if float(match["accuracy"]) < 0.0 or float(match["accuracy"]) > 1.0:
                    raise ValueError(f'YARA rule accuracy is out-of-bounds: {match}')
                match_accuracies.append(float(match["accuracy"]))

            return 1.0 * max(match_accuracies)
        return 0.5

    def _populate_data(self, results):
        if results:
            return {
                "outcome": "RuleMatch",
                "meta": [result.meta for result in results],
            }
        return {"outcome": "NoRuleMatch"}

    def prepare(self) -> bool:
        # Check cache directory
        if not path.exists(self.cache_dir):
            try:
                makedirs(self.cache_dir)
            except OSError as e:
                raise OSError(f"Unable to create cache directory: {e}") from e

        # Compile YARA rules
        try:
            files = glob(self.rules)
            yara_rules = {}
            for file in files:
                with open(file, "r", encoding="utf-8") as f:
                    yara_rules[file] = f.read()

            compiled_rules = yara.compile(sources=yara_rules)
            compiled_rules.save(self.compiled)

            if not path.isfile(self.compiled):
                raise FileNotFoundError(f'Unable to locate compiled YARA rules: {e}')

            return True
        except OSError as e:
            raise OSError(f"Unable to read YARA rules: {e}") from e
        except yara.SyntaxError as e:
            raise yara.SyntaxError(f"Syntax error when compiling YARA rules: {e}") from e
        except yara.Error as e:
            raise yara.Error(f"Unable to compile YARA rules: {e}") from e

    def initialize(self) -> yara.Rules:
        if not path.isfile(self.compiled):
            bt.logging.warning("Compiled YARA rules not found. Running preparation mid-flight.")
            if not self.prepare():
                raise yara.Error('Unable to prepare YARA engine')
        try:
            rules = yara.load(self.compiled)
            return rules
        except yara.Error as e:
            raise yara.Error(f"Unable to load rules: {e}") from e
    
    def execute(self, rules: yara.Rules) -> bool:

        if not self.prompt:
            raise ValueError('Cannot execute engine with empty input')

        if not isinstance(self.prompt, str):
            raise ValueError(f'Input must be a string. The type for the input {self.prompt} is: {type(self.prompt)}')
        
        try:
            results = rules.match(data=self.prompt)
        except yara.TimeoutError as e:
            raise yara.TimeoutError(f'YARA matching timed out: {e}') from e
        except yara.Error as e:
            raise yara.TimeoutError(f'YARA matching returned an error: {e}') from e

        self.output = self._populate_data(results)
        self.confidence = self._calculate_confidence()

        bt.logging.debug(f"YARA engine executed (Confidence: {self.confidence} - Output: {self.output})")
        return True