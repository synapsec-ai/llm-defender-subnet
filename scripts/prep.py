"""
This script prepares the engines before miner is executed.
"""
import sys
import os
from llm_defender.core.miners.engines.prompt_injection import (
    text_classification,
    vector_search,
    heuristics,
)


def prepare_engines():
    """Prepare the engines"""
    # Prepare text classification engine

    # Make directories
    if not os.path.exists(f"{os.path.expanduser('~')}/.llm-defender-subnet"):
        os.makedirs(f"{os.path.expanduser('~')}/.llm-defender-subnet")
    
    text_classification_engine = text_classification.TextClassificationEngine(
        prompt=None, prepare_only=True
    )
    if not text_classification_engine.prepare():
        print("Unable to prepare text classification engine")
        sys.exit(1)

    print("Successfully downloaded the files for the text classification engine")

    # Prepare vector search engine
    vector_search_engine = vector_search.VectorEngine(prompt=None, prepare_only=True)
    if not vector_search_engine.prepare():
        print("Unable to prepare vector search engine")
        sys.exit(1)

    print("Successfully downloaded the files for the vector search engine")

    # Prepare heuristic sub-engines
    yara_engine = heuristics.HeuristicsEngine.YaraSubEngine(prompt=None, weight=1.0)
    if not yara_engine.prepare():
        print("Unable to prepare heuristics:yara engine")
        sys.exit(1)

    print("Successfully downloaded the files for the heuristics engine")


if __name__ == "__main__":
    prepare_engines()
