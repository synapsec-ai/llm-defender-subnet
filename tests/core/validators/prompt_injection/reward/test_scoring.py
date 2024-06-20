import pytest

from llm_defender import prompt_injection_scoring

@pytest.fixture
def engine_response():
    return {
        "confidence": 0.8,
    }


def test_prompt_injection_scoring.calculate_distance_score(engine_response):
    target = 0.5
    distance_score = prompt_injection_scoring.calculate_distance_score(target, engine_response)
    assert isinstance(distance_score, float)


def test_prompt_injection_scoring.calculate_total_distance_score():
    distance_scores = [0.1, 0.2, 0.3]
    total_distance_score = prompt_injection_scoring.calculate_total_distance_score(distance_scores)
    assert isinstance(total_distance_score, float)


def test_prompt_injection_scoring.calculate_subscore_speed():
    timeout = 10.0
    response_time = 5.0
    subscore_speed = prompt_injection_scoring.calculate_subscore_speed(timeout, response_time)
    assert isinstance(subscore_speed, float)


def test_validate_response():
    hotkey = "test_hotkey"
    response = {
        "confidence": 0.8,
    }
    is_valid = validate_response(hotkey, response)
    assert isinstance(is_valid, bool)


def test_prompt_injection_scoring.get_engine_response_object():
    total_score = 0.7
    final_distance_score = 0.3
    final_speed_score = 0.5
    distance_penalty = 0.1
    speed_penalty = 0.2
    raw_distance_score = 0.4
    raw_speed_score = 0.6
    engine_response_object = prompt_injection_scoring.get_engine_response_object(
        total_score, final_distance_score, final_speed_score,
        distance_penalty, speed_penalty, raw_distance_score, raw_speed_score
    )
    assert isinstance(engine_response_object, dict)


def test_prompt_injection_scoring.get_response_object():
    uid = "test_uid"
    hotkey = "test_hotkey"
    target = 0.8
    synapse_uuid = "test_synapse_uuid"
    analyzer = "test_analyzer"
    category = "test_category"
    prompt = "test_prompt"
    response_object = prompt_injection_scoring.get_response_object(
        uid, hotkey, target, synapse_uuid, analyzer, category, prompt
    )
    assert isinstance(response_object, dict)
