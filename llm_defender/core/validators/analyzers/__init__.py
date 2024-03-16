from .prompt_injection.process import process_response as prompt_injection_process


class AnalyzersTypes:
    PROMPT_INJECTION = "Prompt Injection"
    SENSITIVE_DATA = "Sensitive Data"


class Analyzers(AnalyzersTypes):
    @staticmethod
    def process_analyzer(analyzer_type, *args, **kwargs):
        return {
            AnalyzersTypes.PROMPT_INJECTION: prompt_injection_process,
        }.get(analyzer_type)
