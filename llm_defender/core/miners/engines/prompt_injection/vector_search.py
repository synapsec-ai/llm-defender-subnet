"""
This module implements the base-engine used by the prompt-injection
feature of the llm-defender-subnet.
"""
import sys
import uuid
from os import path
import chromadb
import bittensor as bt
from datasets import load_dataset
from llm_defender.base.engine import BaseEngine


class VectorEngine(BaseEngine):
    """Distance-based detection of prompt injection.

    This class implements an engine that uses vector embeddings to
    determine how similar a given prompt is when compared against known
    prompt injections that are stored in chromadb.

    Upon initialization, the default implementation stores known
    prompt-injection strings from publicly available datasets within a
    locally persisted chromadb.

    Attributes:
        db_path:
            An instance of str depicting the path to store the chromadb
        prompt:
            An instance of str depicting the prompt to be searched for
        result_count:
            An instance of int indicating how many results to return
            from the collection
        threshold:
            An instance of float indicating the cut-off point for when a
            match is considered good enough to be accounted for.
        engine_name:
            An instance of str depicting the name for the engine,
            default to "Vector Search"

    Methods:
        get_collection(): Returns the chromadb collection
    """

    def __init__(
        self,
        prompt: str,
        result_count: int = 2,
        threshold: float = 1.0,
        engine_name="Vector Search",
        prepare_only=False
    ):
        super().__init__(prompt, engine_name)

        self.result_count = result_count
        self.threshold = threshold
        self.db_path = f"{path.expanduser('~')}/.llm-defender-subnet/chromadb/"
        
        if not prepare_only:
            self.collection = self.get_collection()
            self.engine_data = self.execute_query()
            self.confidence = self.calculate_confidence()

            if 0.0 <= self.confidence >= 1.0:
                bt.logging.error(f"Confidence out-of-bounds: {self.confidence}")
                self.confidence = 0.0

    def prepare(self) -> bool:
        """This function is used by prep.py
        
        The prep.py executes the prepare methods from all engines before
        the miner is launched. If you change the models used by the
        engines, you must also change this prepare function to match.

        For the vector search engine, the accuracy is highly dependent
        of the contents in the vector database. As a part of the
        fine-tuning of the engines, it is recommended to adjust what
        information is loaded into the chromadb as this code is
        executed.
        """
        try:
            client = chromadb.PersistentClient(path=self.db_path)
            collection = client.get_or_create_collection(
                name="prompt-injection-strings"
            )
        except Exception as e:
            print(f"Unable to initialize chromadb: {e}")
            return False

        try:
            # If we have already initialized the chromadb, we do not need to populate it
            if collection.count() > 0:
                return True

            # Populate chromadb
            dataset = load_dataset("deepset/prompt-injections", split="train", cache_dir=self.cache_dir)

            collection.add(
                documents=dataset["text"],
                ids=[str(uuid.uuid4()) for _ in range(len(dataset["text"]))],
            )

            # Dummy query to trigger the download of the cached onnx model
            collection.query(
                query_texts="foo",
                n_results=1,
                include=["documents", "distances"],
            )

        except Exception as e:
            print(f'Error: {e}')
            return False
        
        return True


    def get_collection(self) -> chromadb.Collection:
        """Returns the chromadb collection.

        Returns:
            collection:
                An instance of chromadb.collection consisting of the
                collection used to store the prompt injection records
        """
        try:
            client = chromadb.PersistentClient(path=self.db_path)
            collection = client.get_collection(
                name="prompt-injection-strings"
            )
        except Exception as e:
            bt.logging.error(f"Unable to get collection from chromadb: {e}")
            sys.exit()

        return collection

    def execute_query(self) -> chromadb.QueryResult:
        """This method executes query against the collection.

        The collection is queried based on the parameters defined in the
        init function.

        Returns:
            query_results: An instance of chromadb.QueryResult
            displaying the query results.
        """

        print("kukkuu")
        try:
            query_result = self.collection.query(
                query_texts=self.prompt,
                n_results=self.result_count,
                include=["documents", "distances"],
            )
        except Exception as e:
            bt.logging.error(f"Exception occurred while querying chromadb: {e}")

        bt.logging.debug(
            f"Query to chromadb collection executed, results: {query_result}"
        )

        print("kakkuu")
        return query_result

    def calculate_confidence(self) -> float:
        """This method calculates the confidence score for the engine.

        The default algorithm uses the threshold as a cut-off point to
        consider a prompt may be a prompt injection.

        Returns:
            confidence: A float depicting the confidence score.
        """
        self.analyzed = True
        confidence = 0.5
        mean_distance = sum(
            sum(sublist) for sublist in self.engine_data["distances"]
        ) / sum(len(sublist) for sublist in self.engine_data["distances"])
        if not any(
            value < self.threshold
            for results in self.engine_data["distances"]
            for value in results
        ):
            bt.logging.debug(
                f'None of the results {self.engine_data["distances"]} were belong the threshold: {self.threshold}'
            )
            
            mean_distance = 1 - mean_distance + self.threshold
            confidence = min(0.5, max(0.0, mean_distance))
            return confidence

        confidence = max(0.5, 1 - mean_distance)
        bt.logging.debug(
            f"Confidence score set to {confidence} for prompt {self.prompt}"
        )

        return confidence

