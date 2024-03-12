
from .reward.scoring import PromptInjectionScoring
from llm_defender.core.exceptions import UIDValidationFailed


def process_response(*,
    metagraph,
    uid,
    query,
    synapse_uuid,
    response,
    score,
    miner_responses
):
    # Get the hotkey for the response
    hotkey = metagraph.hotkeys[uid]
    target = query["label"]
    prompt = query["prompt"]
    weight = query["weight"]
    invalid_uids = []
    # Get the default response object
    response_object = PromptInjectionScoring.get_response_object(
        uid, hotkey, target, prompt, synapse_uuid
    )

    # Set the score for invalid responses to 0.0
    if not PromptInjectionScoring.validate_response(hotkey, response.output):
        score, _, _ = PromptInjectionScoring.assign_score_for_uid(
            score, uid, 0.0, 0.0, weight
        )
        raise UIDValidationFailed(uid)

    # Calculate score for valid response
    scored_response = PromptInjectionScoring.calculate_score(
        response=response.output,
        target=target,
        prompt=prompt,
        response_time=response.dendrite.process_time,
        hotkey=hotkey,
        miner_responses=miner_responses,
        metagraph=metagraph,
    )
    total_score_from_response = scored_response["scores"]["total"]
    score, _, _ = PromptInjectionScoring.assign_score_for_uid(
        score, uid, 0.0, total_score_from_response, weight
    )

    return {
        "prompt": response.output["prompt"],
        "confidence": response.output["confidence"],
        "synapse_uuid": response.output["synapse_uuid"],
        "signature": response.output["signature"],
        "nonce": response.output["nonce"],
        "timestamp": response.output["timestamp"],
                }
