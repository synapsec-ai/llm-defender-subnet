from enum import Enum

from .prompt_injection.analyzer import PromptInjectionAnalyzer
from .prompt_injection.text_classification import TextClassificationEngine
from .sensitive_information.analyzer import SensitiveInformationAnalyzer
from .sensitive_information.token_classification import TokenClassificationEngine

from .prompt_injection import process as prompt_injection_process
from .sensitive_information import process as sensitive_information_process

from .prompt_injection.reward import (
    scoring as prompt_injection_scoring,
    penalty as prompt_injection_penalty,
)

from .sensitive_information.reward import (
    scoring as sensitive_information_scoring,
    penalty as sensitive_information_penalty,
)


class SupportedAnalyzers(Enum):
    PROMPT_INJECTION = "Prompt Injection"
    SENSITIVE_INFORMATION = "Sensitive Information"

    @classmethod
    def is_valid(cls, value):
        return any(value == item.value for item in cls)

    def __str__(self):
        return self.value
