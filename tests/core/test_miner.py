from argparse import ArgumentParser
import pytest
from unittest.mock import patch, MagicMock
from llm_defender.core.miners.miner import LLMDefenderMiner


@pytest.fixture
def mock_prompt_injection_analyzer():
    with patch("llm_defender.core.miners.miner.PromptInjectionAnalyzer"):
        yield MagicMock()


@pytest.fixture
def parser():
    return ArgumentParser()


def test_init(parser, mock_prompt_injection_analyzer):
    miner = LLMDefenderMiner(parser)
    assert miner.neuron_config is not None
