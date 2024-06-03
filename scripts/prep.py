"""
This script prepares the engines before miner is executed.
"""
import sys

import llm_defender.core.miner as LLMDefenderCore

def prepare_engines():
    """Prepare the engines"""
    # Prepare text classification engines
    if not LLMDefenderCore.TextClassificationEngine().prepare():
        print("Unable to prepare text classification engine for prompt injection")
        sys.exit(1)

    if not LLMDefenderCore.TokenClassificationEngine().prepare():
        print("Unable to prepare text classification engine for sensitive information")
        sys.exit(1)
    print("Prepared Text Classification engines")

if __name__ == "__main__":
    prepare_engines()
