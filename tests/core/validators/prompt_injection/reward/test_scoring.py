import pytest

from llm_defender.core.validators.analyzers.prompt_injection.reward.scoring import calculate_distance_score, \
    calculate_total_distance_score, calculate_subscore_speed, validate_response, \
    get_engine_response_object, get_response_object


@pytest.fixture
def engine_response():
    return {
        "confidence": 0.8,
    }


def test_calculate_distance_score(engine_response):
    target = 0.5
    distance_score = calculate_distance_score(target, engine_response)
    assert isinstance(distance_score, float)


def test_calculate_total_distance_score():
    distance_scores = [0.1, 0.2, 0.3]
    total_distance_score = calculate_total_distance_score(distance_scores)
    assert isinstance(total_distance_score, float)


def test_calculate_subscore_speed():
    timeout = 10.0
    response_time = 5.0
    subscore_speed = calculate_subscore_speed(timeout, response_time)
    assert isinstance(subscore_speed, float)


def test_validate_response():
    hotkey = "test_hotkey"
    response = {
        "confidence": 0.8,
    }
    is_valid = validate_response(hotkey, response)
    assert isinstance(is_valid, bool)


def test_get_engine_response_object():
    total_score = 0.7
    final_distance_score = 0.3
    final_speed_score = 0.5
    distance_penalty = 0.1
    speed_penalty = 0.2
    raw_distance_score = 0.4
    raw_speed_score = 0.6
    engine_response_object = get_engine_response_object(
        total_score, final_distance_score, final_speed_score,
        distance_penalty, speed_penalty, raw_distance_score, raw_speed_score
    )
    assert isinstance(engine_response_object, dict)


def test_get_response_object():
    uid = "test_uid"
    hotkey = "test_hotkey"
    target = 0.8
    synapse_uuid = "test_synapse_uuid"
    analyzer = "test_analyzer"
    category = "test_category"
    prompt = "test_prompt"
    response_object = get_response_object(
        uid, hotkey, target, synapse_uuid, analyzer, category, prompt
    )
    assert isinstance(response_object, dict)
