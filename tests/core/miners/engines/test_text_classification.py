import pytest
from unittest.mock import MagicMock, patch

from llm_defender import TextClassificationEngine


@pytest.fixture
def mock_transformers():
    with patch(
            "llm_defender.core.miners.analyzers.prompt_injection.text_classification.AutoModelForSequenceClassification") as mock_model:
        with patch(
                "llm_defender.core.miners.analyzers.prompt_injection.text_classification.AutoTokenizer") as mock_tokenizer:
            with patch(
                    "llm_defender.core.miners.analyzers.prompt_injection.text_classification.pipeline") as mock_pipeline:
                yield mock_model, mock_tokenizer, mock_pipeline


def test_text_classification_engine_execute(mock_transformers):
    mock_model, mock_tokenizer, mock_pipeline = mock_transformers
    mock_model.from_pretrained.return_value = MagicMock()
    mock_tokenizer.from_pretrained.return_value = MagicMock()
    mock_pipe_result = [{"label": "SAFE", "score": 0.8}]
    mock_pipeline.return_value = MagicMock(return_value=mock_pipe_result)

    prompt = "Test prompt"
    engine = TextClassificationEngine(prompts=[prompt])
    engine.prepare()
    engine.execute(model=mock_model, tokenizer=mock_tokenizer)

    assert engine.output == {"outcome": "SAFE", "score": 0.8}
    assert engine.confidence == 0.0
