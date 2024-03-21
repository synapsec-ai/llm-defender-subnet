from llm_defender.base.utils import (
    EngineResponse, validate_numerical_value, normalize_list, validate_miner_blacklist,
    validate_uid, validate_response_data, validate_prompt
)


def test_engine_response():
    response = EngineResponse(0.5, {"key": "value"}, "test")
    assert response.confidence == 0.5
    assert response.data == {"key": "value"}
    assert response.name == "test"
    assert response.get_dict() == {"name": "test", "data": {"key": "value"}, "confidence": 0.5}


def test_validate_numerical_value():
    assert validate_numerical_value(5, int, 0, 10) is True
    assert validate_numerical_value(15, int, 0, 10) is False


def test_normalize_list():
    assert normalize_list([1, 2, 3]) == [0.16666666666666666, 0.3333333333333333, 0.5]
    assert normalize_list([1]) == [1.0]


def test_validate_miner_blacklist():
    assert validate_miner_blacklist(None) is False
    assert validate_miner_blacklist([]) is False
    assert validate_miner_blacklist([{"hotkey": "123", "reason": "Test"}]) is True
    assert validate_miner_blacklist([{"hotkey": "123", "reason": "Test"}, {"invalid_key": "value"}]) is False


def test_validate_uid():
    assert validate_uid(100) is True
    assert validate_uid(0) is True
    assert validate_uid(256) is False
    assert validate_uid(-1) is False
    assert validate_uid(True) is False


def test_validate_response_data():
    assert not validate_response_data(None)
    assert not validate_response_data(True)
    assert not validate_response_data({"name": "Test", "confidence": 0.5, "data": {}})
    assert not validate_response_data({"name": "Test", "confidence": 1.5, "data": {"hotkey": "123"}})
    assert validate_response_data({"name": "Test", "confidence": 0.5, "data": {"hotkey": "123"}})


def test_validate_prompt():
    valid_prompt = {
        "analyzer": "test",
        "category": "test",
        "label": 1,
        "weight": 0.5,
        "hotkey": "123",
        "synapse_uuid": "uuid",
        "created_at": "2024-03-18",
    }
    assert validate_prompt(valid_prompt) is True

    invalid_prompt = {
        "analyzer": "test",
        "category": "test",
        "label": "invalid",
        "weight": 1.5,
        "hotkey": "123",
        "synapse_uuid": "uuid",
        "created_at": "2024-03-18",
    }
    assert validate_prompt(invalid_prompt) is False
