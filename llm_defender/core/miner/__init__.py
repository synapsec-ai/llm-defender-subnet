from enum import Enum

# Core modules for the miner
from .miner import SubnetMiner

from .prompt_injection import (
    PromptInjectionAnalyzer,
    TextClassificationEngine
)

from .sensitive_information import (
    SensitiveInformationAnalyzer,
    TokenClassificationEngine
)

class SupportedAnalyzers(Enum):
    PROMPT_INJECTION = "Prompt Injection"
    SENSITIVE_INFORMATION = "Sensitive Information"

    @classmethod
    def is_valid(cls, value):
        return any(value == item.value for item in cls)

    def __str__(self):
        return self.value
