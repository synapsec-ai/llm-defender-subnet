import pytest
from unittest.mock import MagicMock, patch

from llm_defender.core.miners.analyzers.prompt_injection.text_classification import TextClassificationEngine


def test_text_classification_engine_execute():
    prompt = "Test prompt"
    engine = TextClassificationEngine()
    result = engine.execute(prompt)

    assert result == {"outcome": "SAFE", "confidence": 0.0}