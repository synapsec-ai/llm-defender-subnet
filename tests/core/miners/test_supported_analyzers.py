from llm_defender import SupportedAnalyzers


def test_is_valid():
    assert SupportedAnalyzers.is_valid("Prompt Injection")
    assert SupportedAnalyzers.is_valid("Sensitive Information")
    assert not SupportedAnalyzers.is_valid("Invalid Analyzer")


def test_str():
    assert str(SupportedAnalyzers.PROMPT_INJECTION) == "Prompt Injection"
    assert str(SupportedAnalyzers.SENSITIVE_INFORMATION) == "Sensitive Information"
