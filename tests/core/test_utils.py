from llm_defender.base.utils import EngineResponse, validate_numerical_value, normalize_list


def test_engine_response():
    response = EngineResponse(0.5, {"key": "value"}, "test")
    assert response.confidence == 0.5
    assert response.data == {"key": "value"}
    assert response.name == "test"
    assert response.get_dict() == {"name": "test", "data": {"key": "value"}, "confidence": 0.5}
