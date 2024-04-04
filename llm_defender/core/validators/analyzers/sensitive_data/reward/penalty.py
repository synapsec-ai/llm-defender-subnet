import bittensor as bt
from llm_defender.base.utils import validate_uid
import bittensor as bt
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np
from llm_defender.base.utils import validate_uid
def check_similarity_penalty(uid, miner_responses):
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

    # def _check_confidence_history(
    #         uid, miner_responses, penalty_name = 'Confidence score similarity'
    #     ):
        
    #     penalty = 0.0
    #     similar_confidences = []
    #     for i, first_response in enumerate(miner_responses):
    #         first_confidence_value = first_response['response']['confidence']
    #         for j, second_response in enumerate(miner_responses):
    #             if i == j:
    #                 continue
    #             second_confidence_value = second_response['response']['confidence']
    #             if abs(first_confidence_value - second_confidence_value) <= 0.03:
    #                 similar_confidences.append([first_confidence_value, second_confidence_value])
        
    #     penalty += len(similar_confidences) * 0.05
    #     bt.logging.trace(
    #     f"Applied penalty score '{penalty}' from rule '{penalty_name}' for UID: '{uid}'. Instances of similar confidences found within tolerance of 0.03: {len(similar_confidences)}"
    #     )
        
    #     return penalty
    penalty = 0.0

    if not validate_uid(uid) or not miner_responses:
        # Apply penalty if invalid values are provided to the function
        return 20.0

    for engine in [
        "sensitive_info:token_classification",
    ]:
        penalty += _check_response_history(uid, miner_responses, engine)
    # penalty += _check_confidence_history(uid, miner_responses)

    return penalty

def check_duplicate_penalty(uid, miner_responses, response):
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

        if "token_classification" in engine:
            if duplicate_percentage > 0.7:
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
            engine_data_iterable = [entry 
                                    for item in miner_responses 
                                    for entry in item.get('engine_data',[])]
            if engine_response[0] in engine_data_iterable:
                penalty += 0.25

            bt.logging.trace(
                f"Applied penalty score '{penalty}' from rule '{penalty_name}' for UID: '{uid}'"
            )
        return penalty

    if not validate_uid(uid) or not miner_responses or not response:
        # Apply penalty if invalid values are provided to the function
        return 20.0

    penalty = 0.0
    for engine in [
        "sensitive_info:token_classification",
    ]:
        penalty += _find_identical_reply(uid, miner_responses, response, engine)
        penalty += _calculate_duplicate_percentage(uid, miner_responses, engine)

    return penalty

def check_base_penalty(uid, miner_responses, response):
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

        # this range denotes miners who perform way better than a purely random guess
        if 0.65 < average_distance <= 0.95:
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
    
    if not validate_uid(uid) or not miner_responses or not response:
        # Apply penalty if invalid values are provided to the function
        return 10.0

    if len(miner_responses) < 15:
        # Apply base penalty if we do not have a sufficient number of responses to process
        bt.logging.trace(f'Applied base penalty for UID: {uid} because of insufficient number of responses: {len(miner_responses)}')
        return 5.0

    penalty = 0.0
    penalty += _check_confidence_validity(uid, response)
    penalty += _check_response_history(uid, miner_responses)

    return penalty
