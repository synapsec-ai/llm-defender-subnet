import os
import time
from datasets import Dataset
import llm_defender.core.validator.prompt_generator as PromptGenerator

only_pi = True

generator = PromptGenerator.PromptGenerator(
    model=os.getenv("VLLM_MODEL_NAME"),
    base_url=os.getenv("VLLM_BASE_URL"),
    api_key=os.getenv("VLLM_API_KEY"),
)
system_messages = []

# Generate prompts
for n in range(0,150):    
    # Prompt Injection
    prompt,messages = generator.construct_pi_prompt(debug=True)
    system_messages += messages

    print(f"\n\nProcessing count: {n}")
    print(f"Prompt Injection Analyzer Prompt (label: {prompt['label']}): \n{prompt['prompt']}\n\nMessages: {messages}\n\n")

    if not only_pi:
        # Sensitive Information
        prompt,messages = generator.construct_si_prompt(debug=True)
        system_messages += messages

        print(f"Sensitive Information Analyzer Prompt (label: {prompt['label']}): \n{prompt['prompt']}\n\nMessages: {messages}")

def list_of_dicts_to_dict_of_lists(list_of_dicts):
    dict_of_lists = {}
    for key in list_of_dicts[0]:
        dict_of_lists[key] = [d[key] for d in list_of_dicts]
    return dict_of_lists

data_dict = list_of_dicts_to_dict_of_lists(system_messages)

# Convert the list of dicts to a Dataset
new_dataset = Dataset.from_dict(data_dict)

# Define the path to save/load the dataset
dataset_path = f"datasets/{str(time.time())}/system_messages"

# Save the dataset to disk
new_dataset.save_to_disk(dataset_path)

print(f"Dataset saved/updated at {dataset_path}")
