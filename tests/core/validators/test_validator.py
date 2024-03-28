import pytest
from unittest.mock import MagicMock, patch
import bittensor as bt

from llm_defender.core.validators.validator import LLMDefenderValidator


@pytest.fixture
def mock_validator_config():
    parser_mock = MagicMock()
    parser_mock.return_value = MagicMock()
    return parser_mock


@pytest.fixture
def mock_bittensor_classes():
    return MagicMock()


@pytest.fixture
def validator_instance(mock_validator_config, mock_bittensor_classes):
    return LLMDefenderValidator(parser=mock_validator_config)


@pytest.fixture
def get_mock_wallet() -> bt.MockWallet:
    wallet = bt.MockWallet(name="mock_wallet", hotkey="mock", path="/tmp/mock_wallet")
    return wallet


@pytest.fixture
def mock_response():
    return {
        "prompt": "Your mock prompt data"
    }


@pytest.fixture
def mock_post_success(mock_response):
    with patch('llm_defender.core.validators.validator.requests.post') as mock_post, \
         patch('llm_defender.core.validators.validator.bt.logging') as mock_logging:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_response
        yield mock_post



@pytest.fixture
def mock_response_failure():
    return {
        "error": "Mock error message"
    }


@pytest.fixture
def mock_post_failure(mock_response_failure):
    with patch('llm_defender.core.validators.validator.requests.post') as mock_post, \
         patch('llm_defender.core.validators.validator.bt.logging') as mock_logging:
        mock_post.return_value.status_code = 400
        mock_post.return_value.json.return_value = mock_response_failure
        yield mock_post


def test_validator_validation(validator_instance, get_mock_wallet):
    metagraph_mock = MagicMock()
    subtensor_mock = MagicMock()
    assert not validator_instance.validator_validation(metagraph_mock, get_mock_wallet, subtensor_mock)


def test_process_responses(validator_instance):
    processed_uids = MagicMock()
    query = {'analyzer': 'Prompt Injection', 'label': 'test_label', 'prompt': 'test_prompt'}
    responses = [MagicMock()]
    synapse_uuid = 'test_uuid'

    with pytest.raises(AttributeError):
        validator_instance.process_responses(processed_uids, query, responses, synapse_uuid)


def test_get_api_prompt_success(mock_post_success, validator_instance):
    prompt = validator_instance.get_api_prompt(
        hotkey='mock_hotkey',
        signature='mock_signature',
        synapse_uuid='mock_synapse_uuid',
        timestamp='mock_timestamp',
        nonce='mock_nonce',
        miner_hotkeys=['mock_miner_hotkey']
    )
    assert prompt == {"prompt": "Your mock prompt data"}


def test_get_api_prompt_failure(mock_post_failure, validator_instance):
    prompt = validator_instance.get_api_prompt(
        hotkey='mock_hotkey',
        signature='mock_signature',
        synapse_uuid='mock_synapse_uuid',
        timestamp='mock_timestamp',
        nonce='mock_nonce',
        miner_hotkeys=['mock_miner_hotkey']
    )
    assert prompt is None


def test_save_miner_state(validator_instance):
    assert validator_instance.save_miner_state() is None


def test_load_miner_state(validator_instance):
    assert validator_instance.load_miner_state() is None


def test_truncate_miner_state(validator_instance):
    assert validator_instance.truncate_miner_state() is None


def test_save_state(validator_instance):
    assert validator_instance.save_state() is None


def test_load_state(validator_instance):
    assert validator_instance.load_state() is None
