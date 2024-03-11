import bittensor as bt
from llm_defender.core.validators import penalty


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
        duplicate += penalty.duplicate.check_penalty(
            uid, miner_responses[hotkey], response
        )

        bt.logging.trace(
            f"Penalty score {[similarity, base, duplicate]} for response '{response}' from UID '{uid}'"
        )
        return similarity, base, duplicate
