
import bittensor as bt

def _calculate_duplicate_percentage(uid, miner_responses, engine, penalty_name="Duplicate percentage"):
    penalty = 0.0
    # Isolate engine-specific data
    engine_data = [entry for item in miner_responses for entry in item.get('engine_data', []) if entry.get('name') == engine]

    if not engine_data:
        return penalty
    
    # Calculate duplicate percentage
    duplicate_percentage = 1 - len(set(str(entry) for entry in engine_data)) / len(engine_data)

    if engine == "engine:yara" and duplicate_percentage > 0.95:
        penalty += 1
    elif engine == "engine:vector_search" and duplicate_percentage > 0.15:
        penalty += 2
    elif engine == "engine:text_classification":
        if duplicate_percentage > 0.5:
            if duplicate_percentage > 0.95:
                penalty += 3
            elif duplicate_percentage > 0.9:
                penalty += 2
            elif duplicate_percentage > 0.8:
                penalty += 1
            else:
                penalty += 0.5

    bt.logging.trace(f"Applied penalty score '{penalty}' from rule '{penalty_name}' for UID: '{uid}'. Duplicate % for {engine}: {duplicate_percentage}")
    return penalty


def _find_identical_reply(uid, miner_responses, response, engine, penalty_name="Identical replies"):
    """Applies penalty if identical replies are found"""
    penalty = 0.0
    engine_responses = [data for data in response.get("engines", []) if data["name"] == engine]
    
    if not engine_responses:
        return penalty
    
    # Extracting the response for comparison
    response_data = set(entry["data"] for entry in engine_responses)
    
    for item in miner_responses:
        for entry in item.get('engine_data', []):
            if entry.get('name') == engine and entry.get('data') in response_data:
                penalty += 0.5
                break  # Exit loop if duplicate is found
    
    bt.logging.trace(f"Applied penalty score '{penalty}' from rule '{penalty_name}' for UID: '{uid}'")
    return penalty


def check_penalty(uid, miner_responses, response):
    """This function checks the total penalty score within duplicate category"""
    if not isinstance(uid, str) or not isinstance(miner_responses, list) or not isinstance(response, dict):
        # Received invalid data from miner, apply max penalty
        return 20.0
    
    penalty = 0.0
    for engine in ["engine:text_classification", "engine:yara", "engine:vector_search"]:
        penalty += _find_identical_reply(uid, miner_responses, response, engine)
        penalty += _calculate_duplicate_percentage(uid, miner_responses, engine)
    
    return penalty

            