import bittensor as bt
from llm_defender.base.utils import validate_uid


def _calculate_duplicate_percentage(
    uid, miner_responses, engine, penalty_name="Duplicate percentage"
):
    """
    Calculates the percentage of duplicate entries for a specific engine in the 
    miner responses & assigns a specific penalty for each engine depending on the 
    associated ercentage value, which is then outputted.

    Arguments:
        uid:
            An int instance displaying a unique user id for a miner. Must be 
            between 0 and 255.
        miner_responses:
            A iterable instance where each element must be a dict instance 
            containing flag 'engine_data'.
            
            Each value associated with the 'engine_data' key must itself be a 
            dict instance containing the flags 'name' and 'data'. 
            
            The 'name' flag should have a value that is a str instance displaying
            the name of the specific engine, and the 'data' flag should have a 
            value that contains the engine outputs.
        engine:
            A str instance displaying the name of the engine that we want to 
            calculate the penalty for.
        penalty_name:
            A str instance displaying the name of the penalty operation being 
            performed. Default is set to 'Duplicate percentage'.

            This generally should not be modified.
    
    Returns:
        penalty:
            A float instance representing the penalty score based on the percent 
            amount of duplicate responses from a set of miner responses.    
    """
    penalty = 0.0
    # Isolate engine-specific data
    engine_data = [
        entry
        for item in miner_responses
        for entry in item.get("engine_data", [])
        if entry.get("name") == engine
    ]
    if not engine_data:
        return penalty

    # Calculate duplicate percentage
    engine_data_str = [str(entry) for entry in engine_data]
    duplicates = {entry: engine_data_str.count(entry) for entry in engine_data_str}
    if not duplicates:
        return penalty
    duplicate_percentage = (len(engine_data) - len(duplicates)) / len(engine_data)

    if not duplicate_percentage:
        return penalty

    if engine == "engine:yara":
        if duplicate_percentage > 0.95:
            penalty += 0.25
    elif engine == "engine:vector_search":
        if duplicate_percentage > 0.15:
            penalty += 0.5
    elif engine == "engine:text_classification":
        if duplicate_percentage > 0.5:
            if duplicate_percentage > 0.95:
                penalty += 1.0
            elif duplicate_percentage > 0.9:
                penalty += 0.66
            elif duplicate_percentage > 0.8:
                penalty += 0.33
            else:
                penalty += 0.15
    bt.logging.trace(
        f"Applied penalty score '{penalty}' from rule '{penalty_name}' for UID: '{uid}'. Duplicate % for {engine}: {duplicate_percentage}"
    )

    return penalty


def _find_identical_reply(
    uid, miner_responses, response, engine, penalty_name="Identical replies"
):
    """
    Applies a penalty if identical replies are found for a specific engine.

    Arguments:
        uid:
            An int instance displaying a unique user id for a miner. Must be between 0
            and 255.
        miner_responses:
            A iterable instance where each element must be a dict instance containing flag 
            'engine_data'.
            
            Each value associated with the 'engine_data' key must itself be a dict 
            instance containing the flags 'name' and 'data'. 
            
            The 'name' flag should have a value that is a str instance displaying
            the name of the specific engine, and the 'data' flag should have a value 
            that contains the engine outputs.
        response:
            A dict instance which must have a flag 'engines' which is a list instance 
            where each element is a dict. This dict should have a flag 'name' which 
            is the name of a specific engine. 
        engine:
            A str instance displaying the name of the engine that we want to calculate 
            the penalty for.
        penalty_name:
            A str instance displaying the name of the penalty operation being performed. 
            Default is set to 'Identical replies'.

            This generally should not be modified.

    Returns:
        penalty:
            A float instance representing the penalty score based whether or not identical
            replies are found for a specific engine.
    """
    penalty = 0.0
    engine_response = [data for data in response["engines"] if data["name"] == engine]
    if not engine_response:
        return penalty
    if len(engine_response) > 0:
        if any(
            engine_response == entry
            for item in miner_responses
            for entry in item.get("engine_data", [])
        ):
            penalty += 0.25

        bt.logging.trace(
            f"Applied penalty score '{penalty}' from rule '{penalty_name}' for UID: '{uid}'"
        )
    return penalty


def check_penalty(uid, miner_responses, response):
    """
    This function checks the total penalty score within duplicate category. 
    This involves a summation of penalty values for the following methods 
    over all engines:
        ---> _find_identical_reply()
        ---> _calculate_duplicate_percentage()
    
    A penalty of 20.0 is also added if any of the inputs (uid, miner_responses, 
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

    if not validate_uid(uid) or not miner_responses or not response:
        # Apply penalty if invalid values are provided to the function
        return 20.0

    penalty = 0.0
    for engine in ["engine:text_classification", "engine:yara", "engine:vector_search"]:
        penalty += _find_identical_reply(uid, miner_responses, response, engine)
        penalty += _calculate_duplicate_percentage(uid, miner_responses, engine)

    return penalty
