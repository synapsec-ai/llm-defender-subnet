import pytest
from unittest.mock import patch, MagicMock
from llm_defender.core.miners.analyzers.sensitive_information.token_classification import TokenClassificationEngine


@pytest.fixture
def mock_transformers():
    with patch('llm_defender.core.miners.analyzers.sensitive_information.token_classification.AutoModelForTokenClassification') as mock_model:
            with patch('llm_defender.core.miners.analyzers.sensitive_information.token_classification.AutoTokenizer') as mock_tokenizer:
                with patch('llm_defender.core.miners.analyzers.sensitive_information.token_classification.pipeline') as mock_pipeline:
                    yield mock_model, mock_tokenizer, mock_pipeline


@pytest.fixture
def mock_cache_dir_exists():
    with patch('os.path.exists') as mock_exists:
        mock_exists.return_value = True
        yield


def test_prepare(mock_cache_dir_exists, mock_transformers):
    mock_model, mock_tokenizer, _ = mock_transformers
    engine = TokenClassificationEngine()
    mock_tokenizer.from_pretrained.return_value = MagicMock()
    mock_model.from_pretrained.return_value = MagicMock()
    assert engine.prepare() == True


def test_initialize(mock_transformers):
    mock_model, mock_tokenizer, _ = mock_transformers
    engine = TokenClassificationEngine()
    engine.initialize()
    mock_model.from_pretrained.assert_called_once()
    mock_tokenizer.from_pretrained.assert_called_once()


def test_execute(mock_transformers):
    mock_model, mock_tokenizer, mock_pipeline = mock_transformers
    mock_model.from_pretrained.return_value = MagicMock()
    mock_tokenizer.from_pretrained.return_value = MagicMock()
    mock_pipeline.return_value = MagicMock(return_value=[{"start": "now", "end": "later", "entity": "PERSON", "score": 0.95}])

    engine = TokenClassificationEngine(prompt="Some sensitive data.")
    engine.initialize()
    engine.execute(mock_model, mock_tokenizer)

    assert engine.output == {
        "outcome": "ResultsFound",
        "token_data": [{'entity': 'PERSON', 'score': 0.95}]
    }
    assert engine.confidence == 0.95
