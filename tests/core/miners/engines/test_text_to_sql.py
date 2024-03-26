import pytest
from unittest.mock import MagicMock, patch
from llm_defender.core.miners.analyzers.prompt_injection.text_to_sql import TextToSqlEngine


@pytest.fixture
def mock_transformers():
    with patch("llm_defender.core.miners.analyzers.prompt_injection.text_to_sql.GPT2LMHeadModel") as mock_model:
        with patch("llm_defender.core.miners.analyzers.prompt_injection.text_to_sql.GPT2Tokenizer") as mock_tokenizer:
            yield mock_model, mock_tokenizer


def test_text_to_sql_engine_execute(mock_transformers):
    mock_model, mock_tokenizer = mock_transformers
    mock_model.from_pretrained.return_value = MagicMock()
    mock_tokenizer.from_pretrained.return_value = MagicMock()
    mock_model.generate.return_value = [[101, 1234, 5678, 102]]
    prompt = "Test prompt"
    mock_tokenizer.decode.return_value = f"{prompt}DELETE FROM users WHERE id = 1;"
    engine = TextToSqlEngine(prompt=prompt)

    with patch("llm_defender.core.miners.analyzers.prompt_injection.text_to_sql.path.exists", return_value=True):
        engine.prepare()

    engine.execute(model=mock_model, tokenizer=mock_tokenizer)
    assert engine.output == {"outcome": "converted", "data": "DELETE FROM users WHERE id = 1;"}
    assert engine.confidence == 1
