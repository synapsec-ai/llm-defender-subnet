import pickle
from argparse import ArgumentParser
from unittest.mock import patch, mock_open, MagicMock

import bittensor as bt
import pytest
from requests import ReadTimeout, JSONDecodeError, ConnectionError

from llm_defender.base.neuron import BaseNeuron


@pytest.fixture
def neuron_instance() -> BaseNeuron:
    parser = ArgumentParser()
    return BaseNeuron(parser, profile="test")


@pytest.fixture
def mock_sign_data():
    with patch('llm_defender.base.neuron.sign_data') as mock_sign:
        mock_sign.return_value = "dummy_signature"
        yield mock_sign


@pytest.fixture
def mock_requests_post():
    with patch("llm_defender.base.neuron.BaseNeuron.requests_post") as mock_post:
        yield mock_post


@pytest.fixture
def get_mock_wallet():
    wallet = bt.MockWallet(name="mock_wallet", hotkey="mock", path="/tmp/mock_wallet")
    return wallet


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


@patch('llm_defender.base.neuron.bt.logging')
@patch('llm_defender.base.neuron.requests.post')
def test_requests_post_successful(mock_post, mock_logging, neuron_instance):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'key': 'value'}
    mock_post.return_value = mock_response
    result = neuron_instance.requests_post(url="https://example.com", headers={}, data={})
    assert result == {'key': 'value'}
    mock_logging.warning.assert_not_called()


@patch('llm_defender.base.neuron.bt.logging')
@patch('llm_defender.base.neuron.requests.post')
def test_requests_post_read_timeout(mock_post, mock_logging, neuron_instance):
    mock_post.side_effect = ReadTimeout("Timeout error")
    neuron_instance.requests_post(url="https://example.com", headers={}, data={})
    mock_logging.error.assert_called_with("Remote API request timed out: Timeout error")


@patch('llm_defender.base.neuron.bt.logging')
@patch('llm_defender.base.neuron.requests.post')
def test_requests_post_json_decode_error(mock_post, mock_logging, neuron_instance):
    mock_post.side_effect = JSONDecodeError("", "test", 1)
    neuron_instance.requests_post(url="https://example.com", headers={}, data={})
    mock_logging.error.assert_called_with("Unable to read the response from the remote API: : line 1 column 2 (char 1)")


@patch('llm_defender.base.neuron.bt.logging')
@patch('llm_defender.base.neuron.requests.post')
def test_requests_post_connection_error(mock_post, mock_logging, neuron_instance):
    mock_post.side_effect = ConnectionError("Connection Error")
    neuron_instance.requests_post(url="https://example.com", headers={}, data={})
    mock_logging.error.assert_called_with("Unable to connect to the remote API: Connection Error")


@patch('llm_defender.base.neuron.bt.logging')
@patch('llm_defender.base.neuron.requests.post')
def test_requests_generic_error(mock_post, mock_logging, neuron_instance):
    mock_post.side_effect = Exception("Generic Exception")
    neuron_instance.requests_post(url="https://example.com", headers={}, data={})
    mock_logging.error.assert_called_with("Generic error during request: Generic Exception")


def test_remote_logger_successful_flow(neuron_instance, mock_sign_data, mock_requests_post, get_mock_wallet):
    mock_requests_post.return_value = {"result": "success"}
    hotkey = get_mock_wallet.hotkey
    result = neuron_instance.remote_logger(hotkey, {"test": "message"})
    assert result


def test_remote_logger_error_flow(neuron_instance, mock_sign_data, mock_requests_post, get_mock_wallet):
    mock_requests_post.return_value = None
    hotkey = get_mock_wallet.hotkey
    result = neuron_instance.remote_logger(hotkey, {"test": "message"})
    assert not result
