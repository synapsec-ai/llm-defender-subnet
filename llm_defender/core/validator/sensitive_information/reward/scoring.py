"""This module processes the incoming response from the miner"""

from bittensor import logging
from copy import deepcopy
from numpy import cbrt, ndarray

# Import custom modules
import llm_defender.base as LLMDefenderBase


def calculate_distance_score(target: float, engine_response: dict) -> float:
    """This function calculates the distance score for a response

    The distance score is a result of the absolute distance for the
    response from each of the engine compared to the target value.
    The lower the distance the better the response is.

    Arguments:
        target:
            A float depicting the target confidence (0.0 or 1.0)

        engine_response:
            A dict containing the individual response produces by an
            engine

    Returns:
        distance:
            A dict containing the scores associated with the engine
    """

    if not LLMDefenderBase.validate_numerical_value(
        engine_response["confidence"], float, 0.0, 1.0
    ):
        return 1.0

    distance = abs(target - engine_response["confidence"])

    return distance


def calculate_total_distance_score(distance_scores: list) -> float:
    """Calculates the final distance score given all responses

    Arguments:
        distance_scores:
            A list of the distance scores

    Returns:
        total_distance_score:
            A float containing the total distance score used for the
            score calculation
    """
    if isinstance(distance_scores, bool) or not isinstance(distance_scores, list):
        return 0.0

    if distance_scores == []:
        return 0.0

    if len(distance_scores) > 1:
        total_distance_score = 1 - sum(distance_scores) / len(distance_scores)
    else:
        total_distance_score = 1 - distance_scores[0]

    return total_distance_score


def calculate_subscore_distance(response, target) -> float:
    """Calculates the distance subscore for the response"""

    # Validate the engine responses and calculate distance score
    distance_scores = []

    if isinstance(response, bool) or not isinstance(response, dict):
        return None

    # If engine response is invalid, return None
    if (
        "engines" not in response.keys()
        or isinstance(response["engines"], bool)
        or not isinstance(response["engines"], list)
        or response["engines"] == []
        or len(response["engines"]) != 1
    ):
        return None

    for _, engine_response in enumerate(response["engines"]):
        if not LLMDefenderBase.validate_response_data(engine_response):
            return None

        distance_scores.append(calculate_distance_score(target, engine_response))

    total_distance_score = calculate_total_distance_score(distance_scores)

    return total_distance_score


def calculate_subscore_speed(timeout, response_time):
    """Calculates the speed subscore for the response"""

    if isinstance(response_time, bool) or not isinstance(response_time, (float, int)):
        return None
    if isinstance(timeout, bool) or not isinstance(timeout, (float, int)):
        return None

    # If response time is 0.0 or larger than timeout, the time is invalid
    if response_time > timeout or response_time <= 0.0 or timeout <= 0.0:
        return None

    speed_score = 1.0 - (cbrt(response_time) / cbrt(timeout))

    return speed_score


def validate_response(hotkey, response) -> bool:
    """This method validates the individual response to ensure it has
    been format correctly

    Arguments:
        response:
            Response received from the miner

    Returns:
        outcome
            An instance of bool depicting the outcome of the validation.
    """
    # Responses without output are not valid
    if not response or isinstance(response, bool):
        logging.trace(f"Received an response without an output: {response}")
        return False

    # Check for type
    if not isinstance(response, dict):
        logging.trace(f"Received an response with incorrect type: {response}")
        return False

    # Check for mandatory keys
    mandatory_keys = [
        "confidence",
        "engines",
        "synapse_uuid",
        "subnet_version",
        "signature",
        "nonce",
        "timestamp",
    ]
    if not all(key in response for key in mandatory_keys):
        logging.trace(
            f"One or more mandatory keys: {mandatory_keys} missing from response: {response}"
        )
        return False

    # Check that the values are not empty
    for key in mandatory_keys:
        if response[key] is None:
            logging.trace(
                f"One or more mandatory keys: {mandatory_keys} are empty in: {response}"
            )
            return False

    # Check signature
    data = (
        f'{response["synapse_uuid"]}{response["nonce"]}{hotkey}{response["timestamp"]}'
    )
    if not LLMDefenderBase.validate_signature(
        hotkey=hotkey, data=data, signature=response["signature"]
    ):
        logging.debug(
            f'Failed to validate signature for the response. Hotkey: {hotkey}, data: {data}, signature: {response["signature"]}'
        )
        return False
    else:
        logging.debug(
            f'Succesfully validated signature for the response. Hotkey: {hotkey}, data: {data}, signature: {response["signature"]}'
        )

    # Check the validity of the confidence score
    if isinstance(response["confidence"], bool) or not isinstance(
        response["confidence"], (float, int)
    ):
        logging.trace(f"Confidence is not correct type: {response['confidence']}")
        return False

    if not 0.0 <= float(response["confidence"]) <= 1.0:
        logging.trace(
            f"Confidence is out-of-bounds for response: {response['confidence']}"
        )
        return False

    # The response has passed the validation
    logging.trace(f"Validation succeeded for response: {response}")
    return True

def get_engine_response_object(
    normalized_analyzer_score: float = 0.0,
    binned_analyzer_score: float = 0.0,
    total_analyzer_raw_score: float = 0.0,
    final_analyzer_distance_score: float = 0.0,
    final_analyzer_speed_score: float = 0.0,
    distance_penalty: float = 0.0,
    speed_penalty: float = 0.0,
    raw_distance_score: float = 0.0,
    raw_speed_score: float = 0.0,
) -> dict:
    """This method returns the score object. Calling the method
    without arguments returns default response used for invalid
    responses."""

    res = {
        "scores": {
            "binned_analyzer_score": binned_analyzer_score,
            "normalized_analyzer_score": normalized_analyzer_score,
            "total_analyzer_raw": total_analyzer_raw_score,
            "distance": final_analyzer_distance_score,
            "speed": final_analyzer_speed_score,
        },
        "raw_scores": {"distance": raw_distance_score, "speed": raw_speed_score},
        "penalties": {"distance": distance_penalty, "speed": speed_penalty},
    }

    return res


def get_response_object(
    uid: str,
    hotkey: str,
    coldkey: str,
    target: float,
    synapse_uuid: str,
    analyzer: str,
    category: str,
    prompt: str,
) -> dict:
    """Returns the template for the response object"""

    response = {
        "UID": uid,
        "hotkey": hotkey,
        "coldkey": coldkey,
        "target": target,
        "prompt": prompt,
        "analyzer": analyzer,
        "category": category,
        "synapse_uuid": synapse_uuid,
        "response": {},
        "analyzer_scored_response": get_engine_response_object(),
        "weight_scores": {"new": 0.0, "old": 0.0, "change": 0.0, "unweighted": 0.0},
        "engine_data": [],
    }

    return response
