import gzip
import random
import os
import bittensor as bt


def get_prompt():
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
        return _get_injection_prompt_from_file()
    elif rand_num <= probabilities_list[0] + probabilities_list[1]:
        bt.logging.trace('Getting safe prompt from file')
        return _get_safe_prompt_from_file()
    elif rand_num <= probabilities_list[0] + probabilities_list[1] + probabilities_list[2]:
        bt.logging.trace('Getting safe prompt from file')
        return _get_safe_prompt_from_file()
    else:
        bt.logging.trace('Getting injection prompt from template')
        return _get_injection_prompt_from_template()


def _get_injection_prompt_from_file():
    template_file_name = "dataset_1.bin.gz"

    # Get the current script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct full paths for template and injection files
    template_file_path = os.path.join(script_dir, "data", template_file_name)

    # Read random line from dataset_1.bin.gz
    with gzip.open(template_file_path, "rb") as templates_file:
        templates = templates_file.readlines()
        prompt = random.choice(templates).decode().strip()

    return {"text": prompt, "isPromptInjection": True}


def _get_safe_prompt_from_file():
    template_file_name = "dataset_0.bin.gz"

    # Get the current script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct full paths for template and injection files
    template_file_path = os.path.join(script_dir, "data", template_file_name)

    # Read random line from dataset_0.bin.gz
    with gzip.open(template_file_path, "rb") as templates_file:
        templates = templates_file.readlines()
        prompt = random.choice(templates).decode().strip()

    return {"text": prompt, "isPromptInjection": False}


def _get_injection_prompt_from_template():
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

    return {"text": prompt, "isPromptInjection": True}
