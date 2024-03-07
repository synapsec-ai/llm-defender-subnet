import bittensor as bt


class LLMDefenderGenericException(Exception):
    def log_to_bittensor(self, *, message, level):
        getattr(bt.logging, level)(message)


class ValidatorNotPresentAtMetagraph(LLMDefenderGenericException):
    pass
