import bittensor as bt
import llm_defender.base as LLMDefenderBase


def check_false_positive_penalty(response, target, log_level):
    """
    This function checks the total penalty score within the false positive category.

    A penalty of 20.0 is added if any of the inputs (uid or miner_responses)
    is not inputted.

    Arguments:
        uid:
            An int instance displaying a unique user id for a miner. Must be
            between 0 and 255.
        miner_responses:
            A iterable instance where each element must be a dict instance
            containing flag 'engine_data'. Each value associated with the
            'engine_data' key must itself be a dict instance containing the
            flags 'name' and 'data'. The 'name' flag should have a value that
            is a str instance displaying the name of the specific engine, and
            the 'data' flag should have a value that contains the engine
            outputs.

    Returns:
        penalty:
            The final penalty value for the _check_response_history() method.
            A penalty of 20.0 is also added if any of the inputs (uid or miner_responses)
            is not inputted.
    """

    def _check_for_false_positives(response, target):
        penalty = 0.0
        
        if target == 0 and response['confidence'] > 0.50:
            penalty += 10.0

        return penalty

    penalty = 0.0

    penalty += _check_for_false_positives(response, target)

    LLMDefenderBase.utils.subnet_logger(
        severity="TRACE",
        message=f"False positive penalty score: {penalty}",
        log_level=log_level
    )

    return penalty


def check_duplicate_penalty(uid, response, log_level):
    """
    This function checks the total penalty score within duplicate category.

    A penalty of 20.0 is added if any of the inputs (uid, miner_responses,
    or response) is not inputted.

    Arguments:
        uid:
            An int instance displaying a unique user id for a miner. Must be
            between 0 and 255.
        miner_responses:
            A iterable instance where each element must be a dict instance
            containing flag 'engine_data'. Each value associated with the
            'engine_data' key must itself be a dict instance containing the
            flags 'name' and 'data'. The 'name' flag should have a value that
            is a str instance displaying the name of the specific engine, and
            the 'data' flag should have a value that contains the engine
            outputs.
        response:
            A dict instance which must have a flag 'engines' which is a list
            instance where each element is a dict. This dict should have a flag
            'name' which is the name of a specific engine.

    Returns:
        penalty:
            The final penalty value for the _find_identical_reply() and
            _calculate_duplicate_percentage() methods. A penalty of 20.0 is
            also added if any of the inputs (uid, miner_responses, or response)
            is not inputted.
    """

    if not LLMDefenderBase.validate_uid(uid) or not response:
        # Apply penalty if invalid values are provided to the function
        return 20.0

    penalty = 0.0

    # penalty += _find_identical_reply(uid, miner_responses, response, "prompt_injection:text_classification",)
    # penalty += _calculate_duplicate_percentage(uid, miner_responses, "prompt_injection:text_classification",)

    LLMDefenderBase.utils.subnet_logger(
        severity="TRACE",
        message=f"Duplicate penalty score: {penalty}",
        log_level=log_level
    )

    return penalty


def check_base_penalty(uid, response, log_level):
    """
    This function checks the total penalty score within the base category.

    It also applies a penalty of 10.0 if invalid values are provided to the function.

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

    def _check_response_validity(uid, response, penalty_name="Response Validity", log_level):
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
                by the _check_response_validity() method. Default is 'Confidence out-of-bounds'.

                This argument generally should not be altered.


        Returns:
            penalty:
                This is a float instance of value 20.0 if the confidence value is out-of-bounds,
                or 0.0 if the confidence value is in bounds (between 0.0 and 1.0).
        """
        penalty = 0.0
        if response["confidence"] > 1.0 or response["confidence"] < 0.0:
            penalty = 20.0

        # Validate engine responses
        if "engines" not in response.keys():

            LLMDefenderBase.utils.subnet_logger(
                severity="TRACE",
                message=f"No engines key in response: {response}",
                log_level=log_level
            )
            
            penalty = 20.0
        else:
            for entry in response["engines"]:

                # Check engine-specific confidence
                if "confidence" not in entry.keys() or (
                    entry["confidence"] > 1.0 or entry["confidence"] < 0.0
                ):
                    
                    LLMDefenderBase.utils.subnet_logger(
                        severity="TRACE",
                        message=f"Confidence out-of-bounds or missing: {response}",
                        log_level=log_level
                    )
                    
                    penalty = 20.0
                    break

        LLMDefenderBase.utils.subnet_logger(
            severity="TRACE",
            message=f"Applied penalty score '{penalty}' from rule '{penalty_name}' for UID: '{uid}'",
            log_level=log_level
        )

        return penalty

    if not LLMDefenderBase.validate_uid(uid) or not response:
        # Apply penalty if invalid values are provided to the function
        bt.logging.debug(f"Validation failed: {uid}, {response}")
        return 10.0

    penalty = 0.0
    penalty += _check_response_validity(uid, response, log_level)

    LLMDefenderBase.utils.subnet_logger(
        severity="TRACE",
        message=f"Base penalty score: {penalty}",
        log_level=log_level
    )

    return penalty
