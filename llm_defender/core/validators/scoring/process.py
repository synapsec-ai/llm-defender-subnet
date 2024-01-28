"""This module processes the incoming response from the miner"""
from bittensor import logging
from torch import Tensor
from copy import deepcopy
import llm_defender.base.utils as utils

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

    if not utils.validate_numerical_value(engine_response["confidence"], float, 0.0, 1.0):
        return 0.0

    distance = abs(target - engine_response["confidence"])

    return distance

def calculate_total_distance_score(distance_scores):
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
    
    if len(distance_scores) > 0:
        total_distance_score = 1 - sum(distance_scores) / len(distance_scores)
    else:
        total_distance_score = 1 - distance_scores
    
    return total_distance_score

def calculate_subscore_distance(response, target) -> list:
    """Calculates the distance subscore for the response"""

    # Validate the engine responses and calculate distance score
    distance_scores = []
    for _,engine_response in response.output["engines"]:
        if not utils.validate_response_data(engine_response):
            return None
        
        distance_scores.append(calculate_distance_score(target, engine_response))

    total_distance_score = calculate_total_distance_score(distance_scores)

    return total_distance_score

def calculate_subscore_speed(timeout, response_time):
    """Calculates the speed subscore for the response"""

    # Calculate score for the speed of the response
    if response_time > timeout:
        return None

    speed_score = 1.0 - (response_time / timeout)

    return speed_score


def validate_response(response) -> bool:
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
    if not response.output or isinstance(response.output, bool):
        logging.trace(f"Received an response without an output: {response.output}")
        return False

    # Check for type
    if not isinstance(response.output, dict):
        logging.trace(f"Received an response with incorrect type: {response.output}")
        return False

    # Check for mandatory keys
    mandatory_keys = [
        "confidence",
        "prompt",
        "engines",
        "synapse_uuid",
        "subnet_version",
    ]
    if not all(key in response.output for key in mandatory_keys):
        logging.trace(
            f"One or more mandatory keys: {mandatory_keys} missing from response: {response.output}"
        )
        return False

    # Check that the values are not empty
    for key in mandatory_keys:
        if response.output[key] is None:
            logging.trace(
                f"One or more mandatory keys: {mandatory_keys} are empty in: {response.output}"
            )
            return False

    # Check the validity of the confidence score
    if isinstance(response.output["confidence"], bool) or not isinstance(
        response.output["confidence"], (float, int)
    ):
        logging.trace(f"Confidence is not correct type: {response.output['confidence']}")
        return False

    if not 0.0 <= float(response.output["confidence"]) <= 1.0:
        logging.trace(f"Confidence is out-of-bounds for response: {response.output['confidence']}")
        return False

    # The response has passed the validation
    logging.trace(f"Validation succeeded for response: {response.output}")
    return True


def assign_score_for_uid(scores: Tensor, uid: int, alpha: float, response_score: float):
    """Assigns a score to an UID

    Arguments:
        scores:
            Current Tensor of scores
        uid:
            UID of the neuron to set the score for
        alpha:
            Scaling factor used for the degradation

    Returns:
        scores:
            An updated Tensor of the scores
    """

    # Ensure the alpha is correctly defined
    if alpha >= 1.0 or not isinstance(alpha, float) or isinstance(alpha, bool):
        logging.error(f"Value for alpha is incorrect: {alpha}")
        raise AttributeError(f"Alpha must be below 1.0. Value: {alpha}")

    # Ensure the response score is correctly defined
    if (
        (0.0 > response_score > 1.0)
        or not isinstance(response_score, float)
        or isinstance(response_score, bool)
    ):
        logging.error(f"Value for response_score is incorrect: {response_score}")
        raise AttributeError(
            f"response_score must be in range (0.0, 1.0). Value: {response_score}"
        )

    # Ensure UID is correctly defined
    if (0 > uid > 255) or not isinstance(uid, int):
        logging.error(f"Value for UID is incorrect: {uid}")
        raise AttributeError(f"UID must be in range (0, 255). Value: {uid}")

    # If current score is already at 0.0 we do not need to do anything
    if response_score == 0.0 and scores[uid] == 0.0:
        return scores, scores[uid]

    old_score = deepcopy(scores[uid])
    logging.trace(f"Assigning score of 0.0 for UID: {uid}. Current score: {old_score}")
    scores[uid] = alpha * scores[uid] + (1 - alpha) * response_score
    logging.trace(f"Assigned score of 0.0 for UID: {uid}. New score: {scores[uid]}")

    if old_score == scores[uid]:
        logging.error(
            f"Score for UID: {uid} did not change. Old score: {old_score}, new score: {scores[uid]}"
        )
        raise ValueError(
            f"Score for UID: {uid} did not change. Old score: {old_score}, new score: {scores[uid]}"
        )

    return scores, old_score

def get_engine_response_object(
    total_score: float = 0.0,
    final_distance_score: float = 0.0,
    final_speed_score: float = 0.0,
    distance_penalty: float = 0.0,
    speed_penalty: float = 0.0,
) -> dict:
    """This method returns the score object. Calling the method
    without arguments returns default response used for invalid
    responses."""

    res = {
        "scores": {
            "total": total_score,
            "distance": final_distance_score,
            "speed": final_speed_score
        },
        "penalties": {"distance": distance_penalty, "speed": speed_penalty},
    }

    return res

def get_response_object(
    uid: str, hotkey: str, target: float, prompt: str, synapse_uuid: str
) -> dict:
    """Returns the template for the response object"""

    response = {
        "UID": uid,
        "hotkey": hotkey,
        "target": target,
        "original_prompt": prompt,
        "synapse_uuid": synapse_uuid,
        "response": {},
        "engine_scores": get_engine_response_object(),
        "weight_scores": {
            "new": 0.0,
            "old": 0.0,
            "change": 0.0,
        },
        "engine_data": [],
    }

    return response
