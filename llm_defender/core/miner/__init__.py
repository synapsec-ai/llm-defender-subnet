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

from .moderation import (
    ModerationAnalyzer,
    ModerationClassificationEngine
)

class SupportedAnalyzers(Enum):
    PROMPT_INJECTION = "Prompt Injection"
    SENSITIVE_INFORMATION = "Sensitive Information"
    MODERATION = "Moderation"


    @classmethod
    def is_valid(cls, value):
        return any(value == item.value for item in cls)

    def __str__(self):
        return self.value
