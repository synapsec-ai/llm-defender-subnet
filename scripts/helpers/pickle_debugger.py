import pickle
import json
from os import path
import argparse

def load_miner_state(validator_hotkey):
    """Loads the miner state from a file"""
    state_path = f"{path.expanduser('~')}/.llm-defender-subnet/{validator_hotkey}_validator_miners.pickle"
    with open(state_path, "rb") as pickle_file:
        miner_responses = pickle.load(pickle_file)

    return miner_responses

def calculate_statistics(data):
    stats = {
        "len": len(data),
        "averages": {
            "total_score": sum(entry["scored_response"]["scores"]["total"] for entry in data) / len(data) if data else None,
            "distance_score": sum(entry["scored_response"]["scores"]["distance"] for entry in data) / len(data) if data else None,
            "speed_score": sum(entry["scored_response"]["scores"]["speed"] for entry in data) / len(data) if data else None,
            "raw_distance": sum(entry["scored_response"]["raw_scores"]["distance"] for entry in data) / len(data) if data else None,
            "raw_speed": sum(entry["scored_response"]["raw_scores"]["speed"] for entry in data) / len(data) if data else None,
            "distance_penalty": sum(entry["scored_response"]["penalties"]["distance"] for entry in data) / len(data) if data else None,
            "speed_penalty": sum(entry["scored_response"]["penalties"]["speed"] for entry in data) / len(data) if data else None
        }
    }

    return stats

# Args
parser = argparse.ArgumentParser()
parser.add_argument("--hotkey", type=str, required=True)
parser.add_argument("--validator_hotkey", type=str, required=True)
args = parser.parse_args()

pickle_data = load_miner_state(args.validator_hotkey)

print(json.dumps(pickle_data[args.hotkey], indent=2))

stats = calculate_statistics(pickle_data[args.hotkey])

print(json.dumps(stats, indent=2))

