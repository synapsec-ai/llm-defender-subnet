from enum import Enum


class SupportedAnalyzers(Enum):
    PROMPT_INJECTION = "Prompt Injection"
    SENSITIVE_INFORMATION = "Sensitive Information"

    @classmethod
    def is_valid(cls, value):
        return any(value == item.value for item in cls)
