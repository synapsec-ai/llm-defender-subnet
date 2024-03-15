import bittensor as bt
from llm_defender.core.validators import penalty
from llm_defender.base.utils import validate_uid


class PenaltyResponse:

    @classmethod
    def get_response_penalties(cls, miner_responses, metagraph, response, hotkey, prompt):
        """This function resolves the penalties for the response"""

        similarity_penalty, base_penalty, duplicate_penalty = cls.apply_penalty(
            miner_responses, metagraph, response, hotkey, prompt
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

    @staticmethod
    def apply_penalty(miner_responses, metagraph, response, hotkey, prompt) -> tuple:
        """
        Applies a penalty score based on the response and previous
        responses received from the miner.
        """

        # If hotkey is not found from list of responses, penalties
        # cannot be calculated.
        if not miner_responses:
            return 5.0, 5.0, 5.0
        if not hotkey in miner_responses.keys():
            return 5.0, 5.0, 5.0

        # Get UID
        uid = metagraph.hotkeys.index(hotkey)

        similarity = base = duplicate = 0.0
        # penalty_score -= confidence.check_penalty(self.miner_responses["hotkey"], response)
        similarity += penalty.similarity.check_penalty(uid, miner_responses[hotkey])
        base += penalty.base.check_penalty(uid, miner_responses[hotkey], response, prompt)
        duplicate += PenaltyResponse.check_penalty(
            uid, miner_responses[hotkey], response
        )

        bt.logging.trace(
            f"Penalty score {[similarity, base, duplicate]} for response '{response}' from UID '{uid}'"
        )
        return similarity, base, duplicate

    @staticmethod
    def check_prompt_response_mismatch(
        uid, response, prompt, penalty_name="Prompt/Response mismatch"
    ):
        """
        Checks if the response's prompt matches the given prompt. If there is a mismatch,
        a penalty of 20.0 is applied. If the response prompt and given prompt do match,
        then a penalty of 0.0 is applied. The penalty is then returned. 

        Arguments:
            uid:
                An int instance displaying a unique user id for a miner. Must be 
                between 0 and 255.
            response:
                A dict instance which must contain the flag 'prompt' containing a str
                instance which displays the exact same prompt as the prompt argument.
            prompt:
                A str instance which displays a prompt. 
            penalty_name:
                A str instance displaying the name of the penalty being administered
                by the check_prompt_response_mismatch() method. Default is 'Prompt/Response
                Mismatch'.
                
                This argument generally should not be altered.

        Returns:
            penalty:
                A float value which will either be 0.0 (response['prompt'] and prompt are
                identical strings), or 20.0 if they are not and there is a prompt/response 
                mismatch.
        """
        penalty = 0.0
        if response["prompt"] != prompt:
            penalty = 20.0
        bt.logging.trace(
            f"Applied penalty score '{penalty}' from rule '{penalty_name}' for UID: '{uid}'"
        )
        return penalty
    
    @staticmethod
    def calculate_duplicate_percentage(
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
    
    @staticmethod
    def find_identical_reply(
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

    @staticmethod
    def check_penalty(uid, miner_responses, response):
        """
        This function checks the total penalty score within duplicate category. 
        This involves a summation of penalty values for the following methods 
        over all engines:
            ---> _find_identical_reply()
            ---> calculate_duplicate_percentage()
        
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
                calculate_duplicate_percentage() methods. A penalty of 20.0 is 
                also added if any of the inputs (uid, miner_responses, or response)
                is not inputted.
        """

        if not validate_uid(uid) or not miner_responses or not response:
            # Apply penalty if invalid values are provided to the function
            return 20.0

        penalty = 0.0
        for engine in ["engine:text_classification", "engine:yara", "engine:vector_search"]:
            penalty += PenaltyResponse.find_identical_reply(uid, miner_responses, response, engine)
            penalty += PenaltyResponse.calculate_duplicate_percentage(uid, miner_responses, engine)

        return penalty
