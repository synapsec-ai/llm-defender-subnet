from argparse import ArgumentParser
from unittest.mock import patch

import bittensor as bt

from llm_defender.base.neuron import BaseNeuron


def test_config():
    parser = ArgumentParser()
    neuron = BaseNeuron(parser=parser, profile="test")

    with patch('os.path.exists', return_value=True):
        config = neuron.config(bt_classes=[bt.MockSubtensor, bt.MockWallet])

    assert config is not None


def test_validate_nonce():
    parser = ArgumentParser()
    neuron = BaseNeuron(parser=parser, profile="test")
    assert neuron.validate_nonce("abc")
    assert not neuron.validate_nonce("abc")
