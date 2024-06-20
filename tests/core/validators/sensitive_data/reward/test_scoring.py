from unittest.mock import patch

import pytest

from llm_defender import sensitive_information_scoring


@pytest.fixture
def mock_utils():
    with patch("llm_defender.base.response_processor.utils") as mock_utils:
        yield mock_utils


@pytest.mark.parametrize(
    "timeout, response_time, expected_subscore",
    [
        (10.0, 5.0, 0.5),
        (10.0, 15.0, None),
        ("10.0", 5.0, None),
    ],
)
def test_calculate_subscore_speed(timeout, response_time, expected_subscore):
    assert sensitive_information_scoring.calculate_subscore_speed(timeout, response_time) == expected_subscore


@pytest.mark.parametrize(
    "total_score, final_distance_score, final_speed_score, distance_penalty, speed_penalty, raw_distance_score, raw_speed_score, expected_response",
    [
        (0.8, 0.6, 0.7, 0.1, 0.2, 0.5, 0.4, {"scores": {"total": 0.8, "distance": 0.6, "speed": 0.7}, "raw_scores": {"distance": 0.5, "speed": 0.4}, "penalties": {"distance": 0.1, "speed": 0.2}}),
        (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, {"scores": {"total": 0.0, "distance": 0.0, "speed": 0.0}, "raw_scores": {"distance": 0.0, "speed": 0.0}, "penalties": {"distance": 0.0, "speed": 0.0}}),
    ],
)
def test_get_engine_response_object(
    total_score,
    final_distance_score,
    final_speed_score,
    distance_penalty,
    speed_penalty,
    raw_distance_score,
    raw_speed_score,
    expected_response,
):
    assert (
        sensitive_information_scoring.get_engine_response_object(
            total_score,
            final_distance_score,
            final_speed_score,
            distance_penalty,
            speed_penalty,
            raw_distance_score,
            raw_speed_score,
        )
        == expected_response
    )
