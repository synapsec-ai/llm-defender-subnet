import gzip
import random
import os
import bittensor as bt
from llm_defender.base.utils import validate_prompt
from datetime import datetime

def serve_response(analyzer: str=None, category: str=None, prompt: str=None, label: int=None, weight: float=None, hotkey: str=None, synapse_uuid: str=None):
    """Serves the response in a standardized format

    Arguments:
        analyzer:
            Determines which analyzer to execute
        category:
            Category for the prompt
        prompt:
            Prompt to be analyzed
        label:
            Expected outcome for the analysis (1 = malicious, 0 = non-malicious)
        weight:
            Weight for the category to be used as a part of the score calculation

    Returns:
        res:
            A dictionary consisting of the arguments given as an input to the function
    """
    
    res = {
        "analyzer": analyzer,
        "category": category,
        "prompt": prompt,
        "label": label,
        "weight": weight,
        "hotkey":hotkey, 
        "synapse_uuid":synapse_uuid,
        "created_at":datetime.now().isoformat()
    }
    if validate_prompt(res):
        return res
    else:
        bt.logging.info(f"Detected invalid prompt: {res}")
        raise ValueError(f"Detected invalid prompt: {res}")

def get_prompt(hotkey, synapse_uuid):
    # Generate random probabilities for three functions
    probabilities_list = [random.random() for _ in range(4)]
    total_probability = sum(probabilities_list)

    # Normalize probabilities to sum up to 1
    probabilities_list = [prob / total_probability for prob in probabilities_list]

    bt.logging.debug(f"Generated probabilities for mock data: {probabilities_list}")

    # Generate a random number within the total probability range
    rand_num = random.uniform(0, 1)

    bt.logging.debug(f"Random value for mock data selection: {rand_num}")

    # Select function based on random number
    if rand_num <= probabilities_list[0]:
        bt.logging.trace('Getting injection prompt from file')
        return _get_injection_prompt_from_file(hotkey, synapse_uuid)
    elif rand_num <= probabilities_list[0] + probabilities_list[1]:
        bt.logging.trace('Getting safe prompt from file')
        return _get_safe_prompt_from_file(hotkey, synapse_uuid)
    elif rand_num <= probabilities_list[0] + probabilities_list[1] + probabilities_list[2]:
        bt.logging.trace('Getting safe prompt from file')
        return _get_safe_prompt_from_file(hotkey, synapse_uuid)
    else:
        bt.logging.trace('Getting injection prompt from template')
        return _get_injection_prompt_from_template(hotkey, synapse_uuid)


def _get_injection_prompt_from_file(hotkey, synapse_uuid):
    template_file_name = "dataset_1.bin.gz"

    # Get the current script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct full paths for template and injection files
    template_file_path = os.path.join(script_dir, "data", template_file_name)

    # Read random line from dataset_1.bin.gz
    with gzip.open(template_file_path, "rb") as templates_file:
        templates = templates_file.readlines()
        prompt = random.choice(templates).decode().strip()

    return serve_response("Prompt Injection", "Dataset", prompt, 1, 0.1, hotkey, synapse_uuid)


def _get_safe_prompt_from_file(hotkey, synapse_uuid):
    template_file_name = "dataset_0.bin.gz"

    # Get the current script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct full paths for template and injection files
    template_file_path = os.path.join(script_dir, "data", template_file_name)

    # Read random line from dataset_0.bin.gz
    with gzip.open(template_file_path, "rb") as templates_file:
        templates = templates_file.readlines()
        prompt = random.choice(templates).decode().strip()

    return serve_response("Prompt Injection", "Dataset", prompt, 0, 0.1, hotkey, synapse_uuid)

def _get_injection_prompt_from_template(hotkey, synapse_uuid):
    template_file_name = "templates.bin.gz"
    injection_file_name = "injections.bin.gz"

    # Get the current script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct full paths for template and injection files
    template_file_path = os.path.join(script_dir, "data", template_file_name)
    injection_file_path = os.path.join(script_dir, "data", injection_file_name)

    # Read random line from templates.bin.gz
    with gzip.open(template_file_path, "rb") as templates_file:
        templates = templates_file.readlines()
        template_line = random.choice(templates).decode().strip()

    # Read random line from injections.bin.gz
    with gzip.open(injection_file_path, "rb") as injections_file:
        injections = injections_file.readlines()
        injection_line = random.choice(injections).decode().strip()

    # Replace [inject-string] with the injection content in the template line
    prompt = template_line.replace("[inject-string]", injection_line)

    return serve_response("Prompt Injection", "Universal", prompt, 1, 0.1, hotkey, synapse_uuid)