import pickle
from argparse import ArgumentParser
from unittest.mock import patch, mock_open

import bittensor as bt
import pytest

from llm_defender.base.neuron import BaseNeuron


@pytest.fixture
def neuron_instance() -> BaseNeuron:
    # Create a BaseNeuron instance for testing
    parser = ArgumentParser()
    return BaseNeuron(parser, profile="test")


def test_config(neuron_instance: BaseNeuron):
    with patch("os.path.exists", return_value=True):
        config = neuron_instance.config(bt_classes=[bt.MockSubtensor, bt.MockWallet])

    assert config is not None


def test_validate_nonce(neuron_instance: BaseNeuron):
    assert neuron_instance.validate_nonce("abc")
    assert not neuron_instance.validate_nonce("abc")


def test_load_used_nonces_file_does_not_exist(neuron_instance: BaseNeuron):
    with patch("os.path.exists") as mock_exists:
        mock_exists.return_value = False
        neuron_instance.load_used_nonces()
        assert neuron_instance.used_nonces == []


def test_load_used_nonces(neuron_instance: BaseNeuron):
    with patch("os.path.exists") as mock_exists:
        mock_exists.return_value = True
        mock_pickle_data = ["test1, test2", "test3", "test4"]

        with patch("builtins.open", mock_open(read_data=pickle.dumps(mock_pickle_data))) as _:
            neuron_instance.load_used_nonces()

        assert neuron_instance.used_nonces == mock_pickle_data
