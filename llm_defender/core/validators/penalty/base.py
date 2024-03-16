import bittensor as bt
from llm_defender.base.utils import validate_uid


def _check_confidence_validity(uid, response, penalty_name="Confidence out-of-bounds"):
    """
    This method checks whether a confidence value is out of bounds (below 0.0, or above 1.0).
    If this is the case, it applies a penalty of 20.0, and if this is not the case the penalty
    will be 0.0. The penalty is then returned.

    Arguments:
        uid:
            An int instance displaying a unique user id for a miner. Must be 
            between 0 and 255.
        response:
            A dict instance which must contain the flag 'confidence' containing a float
            instance representing the confidence score for a given prompt.
        penalty_name:
            A str instance displaying the name of the penalty being administered
            by the _check_confidence_validity() method. Default is 'Confidence out-of-bounds'.
            
            This argument generally should not be altered.


    Returns:
        penalty:
            This is a float instance of value 20.0 if the confidence value is out-of-bounds, 
            or 0.0 if the confidence value is in bounds (between 0.0 and 1.0).
    """
    penalty = 0.0
    if response["confidence"] > 1.0 or response["confidence"] < 0.0:
        penalty = 20.0
    bt.logging.trace(
        f"Applied penalty score '{penalty}' from rule '{penalty_name}' for UID: '{uid}'"
    )
    return penalty


def _check_response_history(
    uid, miner_responses, penalty_name="Suspicious response history"
):
    """
    This method checks the history of a miner's outputted confidence values and determines
    if it is suspicious by taking the average confidence score and applying a penalty based on this.

    Arguments:
        uid:
            An int instance displaying a unique user id for a miner. Must be 
            between 0 and 255.
        miner_responses:
            A iterable instance where each element must be a dict instance containing flag 'confidence',
            and a float value between 0.0 and 1.0 as its associated value.
        penalty_name:
            A str instance displaying the name of the penalty being administered
            by the _check_response_history() method. Default is 'Suspicious response history'.
            
            This argument generally should not be altered.

    Returns:
        penalty:
            A float instance which depends on the average value of the miner's response 
            confidence values. The penalty will be:
                ---> 7.0 if the average confidence score is between 0.45 and 0.55. 
                This is because many of the engines are set to output 0.5 as a default 
                confidence value if the logic cannot be executed, so if the averages are 
                within a tolerance of 0.05 of 0.5 it likely means that the engine logic 
                failed to execute over multiple different scoring attempts.
                ---> 4.0 if the average confidence is lower than 0.45 and greater than
                or equal to 0.35, or if the average confidence is greater than 0.9.
                ---> 6.0 if the average confidence is less than 0.35.
    """
    total_distance = 0
    count = 0
    penalty = 0.0
    for entry in miner_responses:
        if "scored_response" in entry.keys() and "raw_scores" in entry["scored_response"].keys() and "distance" in entry["scored_response"]["raw_scores"].keys():
            bt.logging.trace(f'Going through: {entry}')
            total_distance += entry["scored_response"]["raw_scores"]["distance"]
            count += 1
        # Miner response is not valid, apply base penalty
        else:
            penalty += 10.0
            bt.logging.debug(f'Applied base penalty due to invalid/stale miners.pickle entry: {entry}')
            
            return penalty

    average_distance = total_distance / count if count > 0 else 0

    # penalize miners for suspiciously high distance score
    if 0.95 < average_distance <= 1.0:
        penalty += 10.0
    # this range denotes miners who perform way better than a purely random guess
    elif 0.65 < average_distance <= 0.95:
        penalty += 0.0
    # this range denotes miners who perform better than a purely random guess
    elif 0.55 < average_distance <= 0.65:
        penalty += 2.0
    # miners in this range are performing at roughly the same efficiency as random 
    elif 0.45 <= average_distance <= 0.55:
        penalty += 5.0
    # miners in this range are performing worse than random
    elif 0.0 <= average_distance < 0.45:
        penalty += 10.0

    bt.logging.trace(
        f"Applied penalty score '{penalty}' from rule '{penalty_name}' for UID: '{uid}'. Average distance: '{average_distance}'"
    )

    return penalty

def check_penalty(uid, miner_responses, response):
    """
    This function checks the total penalty score within the base category, which
    contains the methods:

        ---> _check_prompt_response_mismatch()
        ---> _check_confidence_validity()
        ---> _check_response_history()

    It also applies a penalty of 10.0 if invalid values are provided to the function, 
    and a penalty of 5.0 if there is an insufficient number of miner responses to process
    (this is set to 50 responses).
    
    Arguments:
        uid:
            An int instance displaying a unique user id for a miner. Must be 
            between 0 and 255.
        miner_responses:
            A iterable instance where each element must be a dict instance containing 
            flag 'confidence', and a float value between 0.0 and 1.0 as its associated 
            value.
        response:
            A dict instance which must contain the flag 'confidence' containing a float
            instance representing the confidence score for a given prompt and also must 
            contain the flag 'prompt' containing a str instance which displays the exact same 
            prompt as the prompt argument.
        prompt:
            A str instance displaying the given prompt.
    
    Returns:
        penalty:
            The total penalty score within the base category.
    """
    if not validate_uid(uid) or not miner_responses or not response:
        # Apply penalty if invalid values are provided to the function
        return 10.0

    if len(miner_responses) < 50:
        # Apply base penalty if we do not have a sufficient number of responses to process
        bt.logging.trace(f'Applied base penalty for UID: {uid} because of insufficient number of responses: {len(miner_responses)}')
        return 5.0

    penalty = 0.0
    penalty += _check_confidence_validity(uid, response)
    penalty += _check_response_history(uid, miner_responses)

    return penalty
