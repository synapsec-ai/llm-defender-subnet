"""
This module implements the base-engine used by the prompt-injection
feature of the llm-defender-subnet.
"""
import uuid
from os import path, makedirs
import chromadb
from chromadb.config import Settings
import bittensor as bt
from datasets import load_dataset
from llm_defender.base.engine import BaseEngine


class VectorEngine(BaseEngine):
    """
    Distance-based detection of prompt injection.

    This class implements an engine that uses vector embeddings to
    determine how similar a given prompt is when compared against known
    prompt injections that are stored in chromadb.

    Upon initialization, the default implementation stores known
    prompt-injection strings from publicly available datasets within a
    locally persisted chromadb.

    Attributes:
        name (from the BaseEngine located at llm_defender/base/engine.py):
            A str instance displaying the name of the engine. 
        cache_dir (from the BaseEngine located at llm_defender/base/engine.py):
            The cache directory allocated for the engine. 
        db_path:
            An instance of str depicting the path to store the chromadb
        prompt:
            An instance of str depicting the prompt to be searched for.
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
        __init__():
            Initializes the name, prompt, collection_name and reset_on_init
            attributes.
        _calculate_confidence():
            Determines the confidence score for a given prompt being malicious & 
            returns the value which ranges from 0.0 (SAFE) to 1.0 (MALICIOUS).
        _populate_data():
            Returns a dict instance that displays the outputs for the VectorEngine.
        prepare():
            Checks and creates a cache directory if it doesn't exist.
        initialize():
            This method sets up & initializes a chromadb.PersistentClient instance
            for the VectorEngine.
        execute():
            Gets the collection from chromadb.PersistentClient and executes the query before
            updating the output and confidence attributes for the VectorEngine.
        get_collection(): 
            Returns the chromadb collection
    """

    def __init__(
        self,
        prompt: str = None,
        name="engine:vector_search",
        reset_on_init=False
    ):
        """
        Initializes the prompt, collection_name, and reset_on_init attributes 
        for VectorEngine.

        Arguments:
            name:
                Default is 'engine:vector_search'
            prompt:
                A str instance depicting the prompt for the VectorEngine to analyze.
            reset_on_init:
                Default is False.

        Returns:
            None
        """
        super().__init__(name=name)
        self.prompt = prompt
        self.collection_name = "prompt-injection-strings"
        self.reset_on_init = reset_on_init

    def _calculate_confidence(self):
        """
        Returns the confidence value for the VectorEngine by analyzing the results in 
        the output attribute. Values returned will be between 0.0 (SAFE) and 1.0 (MALICIOUS).
        
        Arguments:
            None

        Returns:
            A float value representing the confidence score for a prompt injection attack given
            by the VectorEngine. Outputs will range from 0.0 (SAFE) to 1.0 (MALICIOUS). 0.5
            will be returned by default if no conclusions can be drawn.
        """
        if self.output["outcome"] != "ResultsNotFound":
            # Some distances are above 1.6 -> unlikely to be malicious
            distances = self.output["distances"]
            if any(distance >= 1.6 for distance in distances):
                return 0.0
            if any(distance <= 1.0 for distance in distances):
                return 1.0
            
            # Calculate the value between 0.0 and 1.0 based on the distance from 1.0 to 1.6
            min_distance = 1.0
            max_distance = 1.6

            # Normalize the distances between 1.0 and 1.6 to a range between 0 and 1
            normalized_distances = [(distance - min_distance) / (max_distance - min_distance) for distance in distances]

            # Calculate the mean of normalized distances
            if normalized_distances:
                normalized_mean = sum(normalized_distances) / len(normalized_distances)

                # Interpolate the value between 0.0 and 1.0 based on the normalized_mean
                interpolated_value = 1.0 - normalized_mean

                return interpolated_value
            return 0.5

        return 0.5

    def _populate_data(self, results):
        """
        Returns a dict instance that displays the outputs for the VectorEngine.

        Arguments:
            results:
                The results of executing the query using the collection from 
                chromadb.PersistentClient

        Returns:
            A dict instance which contains a processed version of the inputted results.
            The flag 'outcome' will always be outputted, and the associated value is a 
            str instance which is either 'ResultsFound' or 'ResultsNotFound'. If the 'outcome'
            flag yields a 'ResultsFound' str, then the flags 'distances' and 'documents' will
            also be included in this dict.
        """
        if results:
            return {
                "outcome": "ResultsFound",
                "distances": results["distances"][0],
                "documents": results["documents"][0],
            }
        return {"outcome": "ResultsNotFound"}

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

        Arguments:
            None

        Returns:
            A bool instance. True is returned if the collection can 
            be initialized and chromadb can be populated. 

        Raises:
            OSError:
                The OSError is raised if the cache directory is unable to be created.
            Exception:
                This Exception is raised if the chromadb collection was unable to be 
                obtained, or if the chromadb collection was unable to be populated. 
                This is based on try/except syntax.
        """
        # Check cache directory
        if not path.exists(self.cache_dir):
            try:
                makedirs(self.cache_dir)
            except OSError as e:
                raise OSError(f"Unable to create cache directory: {e}") from e
            
        # Client is needed to prepare the engine
        client = self.initialize()

        # Initialize collection
        try:
            collection = client.get_or_create_collection(name=self.collection_name)
        except Exception as e:
            raise Exception(f"Unable to get or create chromadb collection: {e}") from e

        # Populate chromadb
        try:
            # If there already are items in the collection, reset them
            if collection.count() > 0:
                return True

            dataset = load_dataset(
                "deepset/prompt-injections", cache_dir=self.cache_dir
            )
            filtered_dataset = dataset.filter(lambda x: x["label"] == 1)

            # Add training data
            collection.add(
                documents=filtered_dataset["train"]["text"],
                ids=[
                    str(uuid.uuid4())
                    for _ in range(len(filtered_dataset["train"]["text"]))
                ],
            )

            # Add testing data
            collection.add(
                documents=filtered_dataset["test"]["text"],
                ids=[
                    str(uuid.uuid4())
                    for _ in range(len(filtered_dataset["test"]["text"]))
                ],
            )

            # Trigger the download of onnx model
            collection.query(query_texts="foo")

            return True
        except Exception as e:
            raise Exception(f"Unable to populate chromadb collection: {e}") from e

    def initialize(self) -> chromadb.PersistentClient:
        """
        This method sets up & initializes a chromadb.PersistentClient instance
        for the VectorEngine.

        Arguments:
            None

        Returns:
            A chromadb.PersistentClient instance.
        """
        client = chromadb.PersistentClient(path=f"{self.cache_dir}/chromadb2", settings=Settings(allow_reset=True))
        if self.reset_on_init:
            client.reset()

        return client

    def execute(self, client: chromadb.PersistentClient):
        """
        Gets the collection from chromadb.PersistentClient and executes the query before
        updating the output and confidence attributes for the VectorEngine.

        Arguments:
            client:
                A chromadb.PersistentClient instance returned from the initialize() method.
        
        Returns:
            True bool if no errors are raised. False will not be returned if an error is raised;
            rather None will be returned.

        Raises:
            ValueError:
                The ValueError is raised if client.get_collection() does not work. This is likely
                because the miner was not initiated properly, or if the ChromaDB collection could
                not be found. This is based on try/except syntax.
            Exception:
                The Exception error is raised if the ChromaDB collection is not found or the 
                ChromaDB collection was unable to be obtained.
        """
        # Get collection
        try:
            collection = client.get_collection(name=self.collection_name)
        except ValueError as e:
            bt.logging.warning(
                f"Running preparation mid-flight for chromadb. The miner may not have been initialized properly, consider restarting the miner. Error received: {e}"
            )
            self.prepare()
            collection = client.get_collection(name="prompt-injection-strings")
        except Exception as e:
            raise Exception(f"Unable to get collection from chromadb: {e}") from e

        if not collection:
            raise ValueError("ChromaDB collection not found")

        # Execute query
        try:
            results = collection.query(
                query_texts=self.prompt,
                n_results=2,
                include=["documents", "distances"],
            )
        except Exception as e:
            raise Exception(f"Unable to query documents from collection: {e}") from e

        self.output = self._populate_data(results)
        self.confidence = self._calculate_confidence()

        bt.logging.debug(
            f"Vector Search engine executed (Confidence: {self.confidence} - Output: {self.output})"
        )
        return True
