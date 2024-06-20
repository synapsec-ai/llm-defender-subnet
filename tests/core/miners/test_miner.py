from argparse import ArgumentParser
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def mock_prompt_injection_analyzer():
    with patch("llm_defender.core.miners.miner.PromptInjectionAnalyzer"):
        yield MagicMock()


@pytest.fixture
def parser():
    return ArgumentParser()


@pytest.mark.skip(reason="Test not yet implemented")
def test_init(parser, mock_prompt_injection_analyzer):
    # Import custom modules
    import llm_defender.core.miner as LLMDefenderCore
    miner = LLMDefenderCore.SubnetMiner(parser)
    assert miner.neuron_config is not None
