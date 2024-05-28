"""
This module implements common classes that are used by one or more core
features and their engines.
"""
import gc
import asyncio
import bittensor as bt

class EngineResponse:
    """
    This class implements a consistent way of representing different
    responses produced by the miners.

    Attributes:
        confidence:
            An instance of float displaying the confidence score for a miner.
        data:
            An instance of dict displaying the data associated with the miner's response.
        name:
            An instance of str displaying the name/identifier of the miner.

    Methods:
        __init__():
            Initializes the EngineResponse class with attributes confidence, data & name.
        get_dict()
            Returns a dict representation of the EngineResponse class.
    """

    def __init__(self, confidence: float, data: dict, name: str):
        """
        Initializes the confidence, data & name attributes.

        Arguments:
            confidence:
                An instance of float displaying the confidence score for a miner.
            data:
                An instance of dict displaying the data associated with the miner's response.
            name:
                An instance of str displaying the name/identifier of the miner.

        Returns:
            None
        """
        self.confidence = confidence
        self.data = data
        self.name = name

    def get_dict(self) -> dict:
        """
        This function returns dict representation of the class.

        Arguments:
            None

        Returns:
            dict:
                A dict instance with keys "name", "confidence" and "data"
        """
        return {"name": self.name, "confidence": self.confidence, "data": self.data}

def validate_numerical_value(value, value_type, min_value, max_value):
    """Validates that a given value is a specific type and between the
    given range

    Arguments:
        value
            Value to validate
        type
            Python type  
        min
            Minimum value
        max
            Maximum value
    
    Returns:
        result
            A bool depicting the outcome of the validation
    
    """
    
    if isinstance(value, bool) or not isinstance(value, value_type):
        return False
    
    if (value < min_value) or (value > max_value):
        return False
    
    return True

def normalize_list(input_list: list) -> list:
    """
    This function normalizes a list so that values are between [0,1] and
    they sum up to 1.

    Arguments:
        input_list:
            A list containing values to be normalized. 
        
    Returns:
        normalized_list:
            A list instance. If input_list is length 1, the output will be [1.0]. 
            If there are negative values in input_list, the output will be normalized 
            between abs(min(input_list)) and the maximum value.
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


def cleanup(variables: list = None):
    """
    This is a generic cleanup function
    
    Arguments:
        variables:
            A list containing variables to be cleaned.

    Returns:
        None
    """
    if variables:
        for variable in variables:
            variable = None
            del variable

    gc.collect()

def timeout_decorator(timeout):
    """
    Uses asyncio to create an arbitrary timeout for an asynchronous
    function call. This function is used for ensuring a stuck function
    call does not block the execution indefinitely.

    Inputs:
        timeout:
            The amount of seconds to allow the function call to run
            before timing out the execution.

    Returns:
        decorator:
            A function instance which itself contains an asynchronous
            wrapper().

    Raises:
        TimeoutError:
            Function call has timed out.
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                # Schedule execution of the coroutine with a timeout
                return await asyncio.wait_for(func(*args, **kwargs), timeout)
            except asyncio.TimeoutError:
                # Raise a TimeoutError with a message indicating which function timed out
                raise TimeoutError(
                    f"Function '{func.__name__}' execution timed out after {timeout} seconds."
                )

        return wrapper

    return decorator


def validate_uid(uid):
    """
    This method makes sure that a uid is an int instance between 0 and
    255. It also makes sure that boolean inputs are filtered out as
    non-valid uid's.

    Arguments:
        uid:
            A unique user id that we are checking to make sure is valid.
            (integer between 0 and 255).

    Returns:
        True:
            uid is valid--it is an integer between 0 and 255, True and
            False excluded.
        False:
            uid is NOT valid.
    """
    # uid must be an integer instance between 0 and 255
    if not isinstance(uid, int) or isinstance(uid, bool):
        return False
    if uid < 0 or uid > 255:
        return False
    return True

def validate_response_data(engine_response: dict) -> bool:
    """Validates the engine response contains correct data
    
    Arguments:
        engine_response:
            A dict containing the individual response produces by an
            engine
    
    Returns:
        result:
            A bool depicting the validity of the response
    """
    
    if isinstance(engine_response, bool) or not isinstance(engine_response, dict):
        return False
    
    required_keys = ["name", "confidence", "data"]
    for _,key in enumerate(required_keys):
        if key not in engine_response.keys():
            return False
        if engine_response[key] is None or engine_response[key] == "" or engine_response[key] == [] or engine_response[key] == {} or isinstance(engine_response[key], bool):
            return False
        
        if key == "confidence":
            if not validate_numerical_value(value=engine_response[key], value_type=float, min_value=0.0, max_value=1.0):
                return False
        
    return True

def validate_signature(hotkey: str, data: str, signature: str) -> bool:
    """Validates that the given hotkey has been used to generate the
    signature for data
    
    Arguments:
        hotkey:
            SS58_address of the hotkey used to sign the data
        data:
            Data signed
        signature:
            Signature of the signed data
    
    Returns:
        verdict:
            A bool depicting the validity of the signature
    """
    try:
        outcome = bt.Keypair(ss58_address=hotkey).verify(data, bytes.fromhex(signature))
        return outcome
    except AttributeError as e:
        bt.logging.error(f'Failed to validate signature: {signature} for data: {data} with error: {e}')
        return False
    except TypeError as e:
        bt.logging.error(f'Failed to validate signature: {signature} for data: {data} with error: {e}')
        return False
    except ValueError as e:
        bt.logging.error(f'Failed to validate signature: {signature} for data: {data} with error: {e}')
        return False

def sign_data(hotkey: bt.Keypair, data: str) -> str:
    """Signs the given data with the wallet hotkey
    
    Arguments:
        wallet:
            The wallet used to sign the Data
        data:
            Data to be signed
    
    Returns:
        signature:
            Signature of the key signing for the data
    """
    try:
        signature = hotkey.sign(data.encode()).hex()
        return signature
    except TypeError as e:
        bt.logging.error(f'Unable to sign data: {data} with wallet hotkey: {hotkey.ss58_address} due to error: {e}')
        raise TypeError from e
    except AttributeError as e:
        bt.logging.error(f'Unable to sign data: {data} with wallet hotkey: {hotkey.ss58_address} due to error: {e}')
        raise AttributeError from e

def validate_prompt(prompt_dict):

    # define valid data types for each key to check later
    key_types = {
    'analyzer':str,
    'category':str,
    'label':int,
    'weight':(int, float),
    'hotkey': str,
    'synapse_uuid': str,
    'created_at': str,
    }
    # run checks
    if not isinstance(prompt_dict, dict):
        return False
    if len([pd for pd in prompt_dict]) != len(key_types):
        return False
    for pd in prompt_dict:
        if pd not in ['analyzer','category','label','weight', 'created_at', 'synapse_uuid', 'hotkey']:
            return False 
        if not isinstance(prompt_dict[pd], key_types[pd]):
            return False 
        elif pd == 'label':
            if isinstance(prompt_dict[pd], bool):
                return False
            if prompt_dict[pd] not in [0,1]:
                return False
        elif pd == 'weight':
            if isinstance(prompt_dict[pd], bool):
                return False 
            if not (0.0 < prompt_dict[pd] <= 1.0):
                return False
    return True

def validate_validator_api_prompt_output(api_output):
    """
    Returns a boolean for whether or not the validator's output from the prompt API is valid

  
    """
    if not isinstance(api_output, dict):
        return False 
    
    good_output = True

    type_check_dict = {
        'analyzer': str,
        'category': str,
        'label': int,
        'weight': (int,float)
    }

    for key in type_check_dict:
        if key not in [k for k in api_output]:
            return False

    for key in type_check_dict:

        if not isinstance(api_output[key], type_check_dict[key]):
            good_output = False
            
    if not good_output:        
        bt.logging.trace("Prompt API query validation failed.")
    else:
        bt.logging.trace("Prompt API query validation succeeded.")

    return good_output