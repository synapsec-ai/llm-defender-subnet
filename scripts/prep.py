"""
This script prepares the engines before miner is executed.
"""
import sys
from llm_defender.core.miners.analyzers.prompt_injection.yara import YaraEngine
from llm_defender.core.miners.analyzers.prompt_injection.text_classification import TextClassificationEngine
from llm_defender.core.miners.analyzers.prompt_injection.vector_search import VectorEngine

def prepare_engines():
    """Prepare the engines"""
    # Prepare text classification engine

    if not TextClassificationEngine().prepare():
        print("Unable to prepare text classification engine")
        sys.exit(1)

    print("Prepared Text Classification engine")

    # Prepare vector search engine
    if not VectorEngine().prepare():
        print("Unable to prepare vector search engine")
        sys.exit(1)

    print("Prepared Vector Search engine")

    # Prepare YARA engine
    if not YaraEngine().prepare():
        print("Unable to prepare vector search engine")
        sys.exit(1)

    print("Prepared YARA engine")

if __name__ == "__main__":
    prepare_engines()
