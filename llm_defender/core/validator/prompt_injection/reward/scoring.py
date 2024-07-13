"""This module processes the incoming response from the miner"""

from copy import deepcopy
from numpy import cbrt, log, ndarray

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

    distance = abs(int(target) - engine_response["confidence"])

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


def validate_response(hotkey, response, log_level) -> bool:
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
        LLMDefenderBase.utils.subnet_logger(
            severity="TRACE",
            message=f"Received an response without an output: {response}",
            log_level=log_level
        )
        return False

    # Check for type
    if not isinstance(response, dict):
        LLMDefenderBase.utils.subnet_logger(
            severity="TRACE",
            message=f"Received an response with incorrect type: {response}",
            log_level=log_level
        )
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
        LLMDefenderBase.utils.subnet_logger(
            severity="TRACE",
            message=f"One or more mandatory keys: {mandatory_keys} missing from response: {response}",
            log_level=log_level
        )
        return False

    # Check that the values are not empty
    for key in mandatory_keys:
        if response[key] is None:
            LLMDefenderBase.utils.subnet_logger(
                severity="TRACE",
                message=f"One or more mandatory keys: {mandatory_keys} are empty in: {response}",
                log_level=log_level
            )
            return False

    # Check signature
    data = (
        f'{response["synapse_uuid"]}{response["nonce"]}{hotkey}{response["timestamp"]}'
    )
    if not LLMDefenderBase.validate_signature(
        hotkey=hotkey, data=data, signature=response["signature"], log_level=log_level
    ):
        LLMDefenderBase.utils.subnet_logger(
            severity="DEBUG",
            message=f'Failed to validate signature for the response. Hotkey: {hotkey}, data: {data}, signature: {response["signature"]}',
            log_level=log_level
        )
        return False
    else:
        LLMDefenderBase.utils.subnet_logger(
            severity="DEBUG",
            message=f'Succesfully validated signature for the response. Hotkey: {hotkey}, data: {data}, signature: {response["signature"]}',
            log_level=log_level
        )

    # Check the validity of the confidence score
    if isinstance(response["confidence"], bool) or not isinstance(
        response["confidence"], (float, int)
    ):
        LLMDefenderBase.utils.subnet_logger(
            severity="TRACE",
            message=f"Confidence is not correct type: {response['confidence']}",
            log_level=log_level
        )
        return False

    if not 0.0 <= float(response["confidence"]) <= 1.0:
        LLMDefenderBase.utils.subnet_logger(
            severity="TRACE",
            message=f"Confidence is out-of-bounds for response: {response['confidence']}",
            log_level=log_level
        )
        return False

    # The response has passed the validation
    LLMDefenderBase.utils.subnet_logger(
        severity="TRACE",
        message=f"Validation succeeded for response: {response}",
        log_level=log_level
    )
    return True

def get_normalized_and_binned_scores(total_analyzer_raw_score):
    """
    This function normalizes the analyzer's score using the abs(ln(x)) curve,
    and then bins this normalized value.

    Inputs:
        total_analyzer_raw_score: float
            - The score obtained from the summation of distance/speed scores with
            penalties applied.=

    Outputs:
        normalized_distance_score: float
            - The output of abs(ln(total_analyzer_raw_score))
        binned_distance_score: float
            - The binned output of normalized_distance_score

    """

    if float(total_analyzer_raw_score) == 0.0:
        normalized_distance_score = 10.0
    else:
        normalized_distance_score = abs(log(total_analyzer_raw_score))

    score_bins = [  # [range_low, range_high, binned_score]
        [0, 0.03, 1],
        [0.03, 0.11, 0.9],
        [0.11, 0.22, 0.8],
        [0.22, 0.35, 0.7],
        [0.35, 0.51, 0.6],
        [0.51, 0.69, 0.5],
        [0.69, 0.91, 0.4],
        [0.91, 1.2, 0.3],
        [1.2, 1.6, 0.2],
    ]
    binned_distance_score = 0.1

    for score_bin in score_bins:
        if score_bin[0] <= normalized_distance_score <= score_bin[1]:
            binned_distance_score = score_bin[2]
            break

    return normalized_distance_score, binned_distance_score


def get_engine_response_object(
    normalized_distance_score: float = 0.0,
    binned_distance_score: float = 0.0,
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
            "binned_distance_score": binned_distance_score,
            "normalized_distance_score": normalized_distance_score,
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
        "scored_response": get_engine_response_object(),
        "engine_data": [],
        "weight": 0.1,
    }

    return response
