"""
This script prepares the engines before miner is executed.
"""
import sys

from llm_defender.core.miners.analyzers.prompt_injection.text_classification import (
    TextClassificationEngine as PromptTextClassEngine
)
from llm_defender.core.miners.analyzers.sensitive_information.yara import YaraEngine
from llm_defender.core.miners.analyzers.sensitive_information.token_classification import (
    TokenClassificationEngine as SensitiveTokenClassEngine
)
from llm_defender.core.miners.analyzers.prompt_injection.vector_search import VectorEngine


def prepare_engines():
    """Prepare the engines"""
    # Prepare text classification engines
    if not PromptTextClassEngine().prepare():
        print("Unable to prepare text classification engine for prompt injection")
        sys.exit(1)

    if not SensitiveTokenClassEngine().prepare():
        print("Unable to prepare text classification engine for sensitive information")
        sys.exit(1)
    print("Prepared Text Classification engines")

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
