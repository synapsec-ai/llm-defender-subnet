from llm_defender.core.validators.analyzers.sensitive_data.reward import scoring, penalty
import bittensor as bt
from llm_defender.base import utils

def process_response(
        prompt, response,
        uid,
        target,
        synapse_uuid,
        query,
        validator,
        responses_invalid_uids,
        responses_valid_uids
    ):
    # Get the hotkey for the response
    hotkey = validator.metagraph.hotkeys[uid]
    coldkey = validator.metagraph.coldkeys[uid]

    # Get the default response object
    response_object = scoring.get_response_object(
        uid, hotkey, coldkey, target, synapse_uuid, query["analyzer"], query["category"], query["prompt"]
    )

    # Set the score for invalid responses or responses that fail nonce validation to 0.0
    if not scoring.validate_response(hotkey, response.output) or not validator.validate_nonce(response.output["nonce"]):
        bt.logging.debug(f'Empty response or nonce validation failed: {response}')
        validator.scores, old_score, unweighted_new_score = (
            scoring.assign_score_for_uid(
                validator.scores,
                uid,
                validator.neuron_config.alpha,
                0.0,
                query["weight"],
            )
        )
        responses_invalid_uids.append(uid)

    # Calculate score for valid response
    else:
        response_time = response.dendrite.process_time

        scored_response = calculate_score(prompt, validator,
            response.output, target, response_time, hotkey
        )

        validator.scores, old_score, unweighted_new_score = (
            scoring.assign_score_for_uid(
                validator.scores,
                uid,
                validator.neuron_config.alpha,
                scored_response["scores"]["total"],
                query["weight"],
            )
        )

        miner_response = {
            "confidence": response.output["confidence"],
            "timestamp": response.output["timestamp"],
            "category": response.output["analyzer"],
            "response_time": response_time
        }

        token_class = [
            data
            for data in response.output["engines"]
            if "token_classification" in data["name"]
        ]

        engine_data = []

        if token_class:
            if len(token_class) > 0:
                engine_data.append(token_class[0])

        responses_valid_uids.append(uid)

        if response.output["subnet_version"]:
            if response.output["subnet_version"] > validator.subnet_version:
                bt.logging.warning(
                    f'Received a response from a miner with higher subnet version ({response.output["subnet_version"]}) than yours ({validator.subnet_version}). Please update the validator.'
                )

        # Populate response data
        response_object["response"] = miner_response
        response_object["engine_data"] = engine_data
        response_object["scored_response"] = scored_response
        response_object["weight_scores"] = {
            "new": float(validator.scores[uid]),
            "old": float(old_score),
            "change": float(validator.scores[uid]) - float(old_score),
            "unweighted": unweighted_new_score,
            "weight": query["weight"],
        }

        if validator.wandb_enabled:
            wandb_logs = [
                {
                    f"{response_object['UID']}:{response_object['hotkey']}_confidence": response_object[
                        "response"
                    ][
                        "confidence"
                    ]
                },
                {
                    f"{response_object['UID']}:{response_object['hotkey']}_scores_total": response_object[
                        "scored_response"
                    ][
                        "scores"
                    ][
                        "total"
                    ]
                },
                {
                    f"{response_object['UID']}:{response_object['hotkey']}_scores_distance": response_object[
                        "scored_response"
                    ][
                        "scores"
                    ][
                        "distance"
                    ]
                },
                {
                    f"{response_object['UID']}:{response_object['hotkey']}_scores_speed": response_object[
                        "scored_response"
                    ][
                        "scores"
                    ][
                        "speed"
                    ]
                },
                {
                    f"{response_object['UID']}:{response_object['hotkey']}_raw_scores_distance": response_object[
                        "scored_response"
                    ][
                        "raw_scores"
                    ][
                        "distance"
                    ]
                },
                {
                    f"{response_object['UID']}:{response_object['hotkey']}_raw_scores_speed": response_object[
                        "scored_response"
                    ][
                        "raw_scores"
                    ][
                        "speed"
                    ]
                },
                {
                    f"{response_object['UID']}:{response_object['hotkey']}_weight_score_new": response_object[
                        "weight_scores"
                    ][
                        "new"
                    ]
                },
                {
                    f"{response_object['UID']}:{response_object['hotkey']}_weight_score_old": response_object[
                        "weight_scores"
                    ][
                        "old"
                    ]
                },
                {
                    f"{response_object['UID']}:{response_object['hotkey']}_weight_score_change": response_object[
                        "weight_scores"
                    ][
                        "change"
                    ]
                },
            ]

            for entry in response_object["engine_data"]:
                wandb_logs.append(
                    {
                        f"{response_object['UID']}:{response_object['hotkey']}_{entry['name']}_confidence": entry[
                            "confidence"
                        ]
                    },
                )
            for wandb_log in wandb_logs:
                validator.wandb_handler.log(wandb_log)

            bt.logging.trace(
                f"Adding wandb logs for response data: {wandb_logs} for uid: {uid}"
            )


    bt.logging.debug(f"Processed response: {response_object}")

    return response_object, responses_invalid_uids, responses_valid_uids

def calculate_score(
        prompt, validator, response, target: float, response_time: float, hotkey: str
    ) -> dict:
    """This function sets the score based on the response.

    Returns:
        score:
            An instance of dict containing the scoring information for a response
    """

    # Calculate distance score
    distance_score = scoring.calculate_subscore_distance(response, target)
    if distance_score is None:
        bt.logging.debug(
            f"Received an invalid response: {response} from hotkey: {hotkey}"
        )
        distance_score = 0.0

    # Calculate speed score
    speed_score = scoring.calculate_subscore_speed(
        validator.timeout, response_time
    )
    if speed_score is None:
        bt.logging.debug(
            f"Response time {response_time} was larger than timeout {validator.timeout} for response: {response} from hotkey: {hotkey}"
        )
        speed_score = 0.0

    # Validate individual scores
    if not utils.validate_numerical_value(
        distance_score, float, 0.0, 1.0
    ) or not utils.validate_numerical_value(speed_score, float, 0.0, 1.0):
        bt.logging.error(
            f"Calculated out-of-bounds individual scores (Distance: {distance_score} - Speed: {speed_score}) for the response: {response} from hotkey: {hotkey}"
        )
        return scoring.get_engine_response_object()

    # Set weights for scores
    score_weights = {"distance": 0.85, "speed": 0.15}

    # Get penalty multipliers
    distance_penalty, speed_penalty = get_response_penalties(
        validator,response, hotkey
    )

    # Apply penalties to scores
    (
        total_score,
        final_distance_score,
        final_speed_score,
    ) = validator.calculate_penalized_scores(
        score_weights, distance_score, speed_score, distance_penalty, speed_penalty
    )

    # Validate individual scores
    if (
        not utils.validate_numerical_value(total_score, float, 0.0, 1.0)
        or not utils.validate_numerical_value(final_distance_score, float, 0.0, 1.0)
        or not utils.validate_numerical_value(final_speed_score, float, 0.0, 1.0)
    ):
        bt.logging.error(
            f"Calculated out-of-bounds individual scores (Total: {total_score} - Distance: {final_distance_score} - Speed: {final_speed_score}) for the response: {response} from hotkey: {hotkey}"
        )
        return scoring.get_engine_response_object()

    # Log the scoring data
    score_logger = {
        "hotkey": hotkey,
        "target": target,
        "synapse_uuid": response["synapse_uuid"],
        "score_weights": score_weights,
        "penalties": {"distance": distance_penalty, "speed": speed_penalty},
        "raw_scores": {"distance": distance_score, "speed": speed_score},
        "final_scores": {
            "total": total_score,
            "distance": final_distance_score,
            "speed": final_speed_score,
        },
    }

    bt.logging.debug(f"Calculated score: {score_logger}")

    return scoring.get_engine_response_object(
        total_score=total_score,
        final_distance_score=final_distance_score,
        final_speed_score=final_speed_score,
        distance_penalty=distance_penalty,
        speed_penalty=speed_penalty,
        raw_distance_score=distance_score,
        raw_speed_score=speed_score,
    )

def apply_penalty(validator, response, hotkey) -> tuple:
    """
    Applies a penalty score based on the response and previous
    responses received from the miner.
    """

    # If hotkey is not found from list of responses, penalties
    # cannot be calculated.
    if not validator.miner_responses:
        return 5.0, 5.0, 5.0
    if not hotkey in validator.miner_responses.keys():
        return 5.0, 5.0, 5.0

    # Get UID
    uid = validator.metagraph.hotkeys.index(hotkey)

    similarity = base = duplicate = 0.0
    # penalty_score -= confidence.check_penalty(validator.miner_responses["hotkey"], response)
    similarity += penalty.check_similarity_penalty(
        uid, validator.miner_responses[hotkey]
    )
    base += penalty.check_base_penalty(
        uid, validator.miner_responses[hotkey], response
    )
    duplicate += penalty.check_duplicate_penalty(
        uid, validator.miner_responses[hotkey], response
    )

    bt.logging.trace(
        f"Penalty score {[similarity, base, duplicate]} for response '{response}' from UID '{uid}'"
    )
    return similarity, base, duplicate

def get_response_penalties(validator, response, hotkey):
    """This function resolves the penalties for the response"""

    similarity_penalty, base_penalty, duplicate_penalty = apply_penalty(validator,
        response, hotkey
    )

    distance_penalty_multiplier = 1.0
    speed_penalty = 1.0

    if base_penalty >= 20:
        distance_penalty_multiplier = 0.0
    elif base_penalty > 0.0:
        distance_penalty_multiplier = 1 - ((base_penalty / 2.0) / 10)

    if sum([similarity_penalty, duplicate_penalty]) >= 20:
        speed_penalty = 0.0
    elif sum([similarity_penalty, duplicate_penalty]) > 0.0:
        speed_penalty = 1 - (
            ((sum([similarity_penalty, duplicate_penalty])) / 2.0) / 10
        )

    return distance_penalty_multiplier, speed_penalty
