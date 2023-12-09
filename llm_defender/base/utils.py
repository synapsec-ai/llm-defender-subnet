"""
This module implements common classes that are used by one or more core
features and their engines.
"""
import gc

class EnginePrompt:
    """
    This class implements a consistent way of representing different
    prompts to be analyzed by the subnet.
    """

    def __init__(self, engine: str, prompt: str, data: dict):
        self.prompt = prompt
        self.engine = engine
        self.data = data

    def get_dict(self) -> dict:
        """
        This function returns dict representation of the class
        """
        return {"engine": self.engine, "prompt": self.prompt, "data": self.data}


class EngineResponse:
    """
    This class implements a consistent way of representing different
    responses produced by the miners.
    """

    def __init__(
        self,
        confidence: float,
        engine_data: dict,
        name: str
    ):
        self.confidence = confidence
        self.engine_data = engine_data
        self.name = name


def normalize_list(input_list: list) -> list:
    """
    This function normalizes a list so that values are between [0,1] and
    they sum up to 1.
    """
    if len(input_list) > 1:
        min_val = min(input_list)

        if min_val >= 0:
            # If all values are non-negative, simply divide by sum
            sum_vals = sum(input_list)
            normalized_list = [val / sum_vals for val in input_list]
        else:
            # If there are negative values, normalize between abs(min) and max
            abs_min = abs(min_val)
            adjusted_values = [(val + abs_min) for val in input_list]
            sum_adjusted = sum(adjusted_values)
            normalized_list = [val / sum_adjusted for val in adjusted_values]
    else:
        normalized_list = [1.0]

    return normalized_list

def cleanup(variables: list=None):
    """This is a generic cleanup function"""
    if variables:
        for variable in variables:
            variable = None
            del variable
    
    gc.collect()
 
