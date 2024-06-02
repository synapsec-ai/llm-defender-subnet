from os import path

import pytest

import llm_defender as LLMDefender


def test_init():
    engine = LLMDefender.BaseEngine()
    assert engine.name == "BaseEngine"
    assert engine.prompt is None
    assert engine.confidence is None
    assert engine.output == {}
    assert engine.cache_dir == f"{path.expanduser('~')}/.llm-defender-subnet/cache"


def test_confidence_validation():

    @LLMDefender.BaseEngine.confidence_validation
    def mock_confidence_function(score):
        return score

    assert mock_confidence_function(0.5) == 0.5

    with pytest.raises(ValueError):
        mock_confidence_function(1.5)


def test_data_validation():
    @LLMDefender.BaseEngine.data_validation
    def mock_data_function(data):
        return data

    assert mock_data_function({"key": "value"}) == {"key": "value"}

    with pytest.raises(ValueError):
        mock_data_function({})


class ConcreteEngine(LLMDefender.BaseEngine):
    def _calculate_confidence(self) -> float:
        return 0.75

    def _populate_data(self, results) -> dict:
        return {"result": results}

    def prepare(self) -> bool:
        return True

    def initialize(self):
        ...

    def execute(self):
        ...


def test_get_response():
    engine = ConcreteEngine()
    engine.name = "TestEngine"
    engine.confidence = 0.8
    engine.output = {"key": "value"}
    response = engine.get_response()
    assert response.name == "TestEngine"
    assert response.confidence == 0.8
    assert response.data == {"key": "value"}


def test_calculate_confidence():
    engine = ConcreteEngine()
    confidence = engine._calculate_confidence()
    assert 0.0 <= confidence <= 1.0


def test_populate_data():
    engine = ConcreteEngine()
    dummy_results = {"key1": "value1", "key2": "value2"}
    data = engine._populate_data(dummy_results)
    assert isinstance(data, dict)


def test_prepare():
    engine = ConcreteEngine()
    success = engine.prepare()
    assert isinstance(success, bool)
