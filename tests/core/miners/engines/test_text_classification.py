import argparse

from llm_defender.core.miners.analyzers.prompt_injection.text_classification import TextClassificationEngine


def test_text_classification_engine_execute(mocker):
    args = argparse.Namespace()
    args.status_code = 200
    args.text = "0.0"
    mocker.patch("llm_defender.core.miners.analyzers.prompt_injection.text_classification.requests.post", return_value=args)
    prompt = "Test prompt"
    engine = TextClassificationEngine()
    result = engine.execute(prompt)

    assert result == {"outcome": "SAFE", "confidence": 0.0}