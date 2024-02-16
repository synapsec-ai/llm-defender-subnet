import bittensor as bt
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np
from llm_defender.base.utils import validate_uid


def _check_response_history(
    uid, miner_responses, engine, penalty_name="High-similarity score"
):
    """
    This function assesses the similarity of responses from a specific 
    engine in a miner's response history. It calculates the average cosine 
    similarity of the engine's output data and applies a penalty based on the 
    level of similarity.
    
    Arguments:
        uid:
            An int instance displaying a unique user id for a miner. Must be 
            between 0 and 255.
    miner_responses:
        A iterable instance where each element must be a dict instance 
        containing flag 'engine_data'. Each value associated with the 'engine_data' 
        key must itself be a dict instance containing the flags 'name' and 'data'. 
        The 'name' flag should have a value that is a str instance displaying
        the name of the specific engine, and the 'data' flag should have a value 
        that contains the engine outputs.
    engine:
        A str instance displaying the name of the engine that we want to 
        calculate the penalty for.
    penalty_name:
        A str instance displaying the name of the penalty operation being performed. 
        Default is set to 'High-similarity score'.

        This generally should not be modified.
    
    Returns:
        penalty:
            A float instance representing the penalty score based on the similarity 
            of responses from a specific engine in a miner's response history. 
    """
    # Isolate engine-specific data
    penalty = 0.0
    engine_data = [
        entry
        for item in miner_responses
        for entry in item.get("engine_data", [])
        if entry.get("name") == engine
    ]
    if not engine_data:
        return penalty

    # Calculate duplicsate percentage
    engine_data_str = [str(entry["data"]) for entry in engine_data]

    # Create a CountVectorizer to convert text to word count vectors
    vectorizer = CountVectorizer()

    # Fit and transform the documents into vectors
    vectorized_docs = vectorizer.fit_transform(engine_data_str)

    # Calculate pairwise cosine similarity for all combinations of documents
    cosine_sim_matrix = cosine_similarity(vectorized_docs)

    # Exclude self-similarity values (diagonal) and compute average
    mask = np.triu(np.ones(cosine_sim_matrix.shape), k=1).astype(bool)
    similarities = cosine_sim_matrix[mask]

    if len(similarities) == 0:
        return penalty

    average_similarity = similarities.mean()
    bt.logging.trace(f"Average similarity: {average_similarity}")

    if average_similarity > 0.9:
        penalty += 1.0
    elif average_similarity > 0.8:
        penalty += 0.66
    elif average_similarity > 0.7:
        penalty += 0.33
    elif average_similarity > 0.6:
        penalty += 0.10

    bt.logging.trace(
        f"Applied penalty score '{penalty}' from rule '{penalty_name}' for UID: '{uid}' for engine: '{engine}'. Average similarity: '{average_similarity}'"
    )
    return penalty

#def _check_confidence_history(
#        uid, miner_responses, penalty_name = 'Confidence score similarity'
#    ):
#   
#    penalty = 0.0
#    similar_confidences = []
#   for i, first_response in enumerate(miner_responses):
#        first_confidence_value = first_response['response']['confidence']
#        for j, second_response in enumerate(miner_responses):
#            if i == j:
#                continue
#            second_confidence_value = second_response['response']['confidence']
#            if abs(first_confidence_value - second_confidence_value) <= 0.03:
#                similar_confidences.append([first_confidence_value, second_confidence_value])
#    
#    penalty += len(similar_confidences) * 0.05
#    bt.logging.trace(
#    f"Applied penalty score '{penalty}' from rule '{penalty_name}' for UID: '{uid}'. Instances of similar confidences found within tolerance of 0.03: {len(similar_confidences)}"
#    )
#    
#    return penalty

def check_penalty(uid, miner_responses):
    """
    This function checks the total penalty score within the similarity category. 
    This involves a summation of penalty values for the following methods over 
    all engines:
        ---> _check_response_history()
    
    A penalty of 20.0 is also added if any of the inputs (uid or miner_responses) 
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
    penalty = 0.0

    if not validate_uid(uid) or not miner_responses:
        # Apply penalty if invalid values are provided to the function
        return 20.0

    for engine in ["engine:text_classification", "engine:yara", "engine:vector_search"]:
        penalty += _check_response_history(uid, miner_responses, engine)
#    penalty += _check_confidence_history(uid, miner_responses)

    return penalty
