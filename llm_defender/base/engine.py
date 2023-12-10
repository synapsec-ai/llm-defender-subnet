"""
This module implements the BaseEngine class that must be inherited by
all of the engines used by the llm-defender-subnet. This class
implements some of the fundamental features required by the engines as
well as providing abstract methods the engine classes must implement.

This BaseEngine should be used by all the analyzers. 
"""
from os import path
from typing import Callable
from abc import abstractmethod
from llm_defender.base.utils import EngineResponse


class BaseEngine:
    """BaseEngine for llm-defender-subnet

    This class implements the BaseEngine that should be used by the
    specialized engines used to detect various attacks against LLM
    applications. The actual logic for the detections should be
    implemented in the engines inheriting this class.

    Attributes:
        name:
            An instance of str displaying the name of the engine
        input:
            The engine input that should be analyzed. The type is dependent on the engine.
        output:
            An instance of dict providing the output of the engine analysis
        confidence:
            An instance of float displaying the confidence score of the analysis
        cache_dir:
            The cache directory allocated for the engine.

    Methods:
        _calculate_confidence():
            Calculates the confidence. Should be invoked by the execute() function.
        _populate_data():
            Populates the engine data object. Should be invoked by the execute() function.
        get_response():
            Returns the analysis results. Should be executed for every input after the execute() function has completed.
        prepare():
            Prepares the engine. Is executed during installation.
        initialize():
            Initializes the engine. Is executed once during miner startup.
        execute():
            Executes the engine and analyzes the given input. Is executed for every input handled by the engine.


    """

    def __init__(self, name: str = "BaseEngine"):
        self.input = None
        self.confidence = None
        self.output = {}
        self.name = name
        self.cache_dir = (
            f"{path.expanduser('~')}/.llm-defender-subnet/{self.name}/cache"
        )

    @staticmethod
    def confidence_validation(func: Callable) -> Callable:
        """Validates the confidence score.

        The confidence score returned by the engine must be a float and
        in range of (0.0, 1.0).

        Raises:
            TypeError:
                Return value is not a float
            ValueError:
                Return value is empty
            ValueError:
                Return value is not in range of (0.0, 1.0)
        """

        def wrapper(*args, **kwargs) -> float:
            result = func(*args, **kwargs)
            if not result:
                raise ValueError("Return value must not be empty")
            if not isinstance(result, float):
                raise TypeError("Return value must be float")
            if not 0.0 <= result <= 1:
                raise ValueError("Return value must be in range of (0.0, 1.0)")
            return result

        return wrapper

    @staticmethod
    def data_validation(func: Callable) -> Callable:
        """Validates the engine data.

        The data returned by the engine must be a dict and must not be
        empty.

        Raises:
            TypeError:
                Return value is not a dict
            ValueError:
                Return value is empty
            ValueError:
                Return value contains keys with empty values
        """

        def wrapper(*args, **kwargs) -> dict:
            result = func(*args, **kwargs)
            if not result:
                raise ValueError("Return value must not be empty")
            if not isinstance(result, dict):
                raise TypeError("Return value must be dict")
            if any(value == "" for value in result.values()):
                raise ValueError("Return contains keys with empty values")
            return result

        return wrapper

    @abstractmethod
    @confidence_validation
    def _calculate_confidence(self) -> float:
        """Calculates the confidence of the analysis.

        This method should calculate the confidence of the analysis
        process, meaning that it should output a value in range (0.0,
        1.0) depending on how confident the engine is that the given
        input is malicious.

        A score of 1.0 means the engine is extremely confidence the
        input is malicious. A score of 0.0 means the engine is extremely confident the input
        is not malicious.

        Returns:
            confidence:
                An instance of float depicting the confidence score of the engine

        Raises:
            TypeError:
                Return value is not a dict
            ValueError:
                Return value is empty
            ValueError:
                Return value contains keys with empty values
        """

    @abstractmethod
    @confidence_validation
    def _populate_data(self) -> dict:
        """Populates the data object of the analysis.

        This method should populate the data object. The data can be
        arbitrary in nature but should consist of a proof of the
        analysis work.

        Returns:
            data:
                An instance of dict containing the engine output data

        Raises:
            TypeError:
                Return value is not a dict
            ValueError:
                Return value is empty fd
            ValueError:
                Return value is not in range of (0.0, 1.0)
        """

    def get_response(self) -> EngineResponse:
        """Returns the outcome of the object.

        This method returns the response from the engine in a correct
        format so that it can be properly handled in the downstream
        handlers.

        Prior to calling this method, self.confidence and self.data
        should be populated based on the return values from
        calculate_confidence() and populate_data() methods.
        """

        if not self.name or not self.confidence or not self.output:
            raise ValueError(
                f"Instance attributes [self.name, self.confidence, self.data] cannot be empty. Values are: {[self.name, self.confidence, self.output]}"
            )

        if not isinstance(self.name, str):
            raise TypeError("Name must be a string")

        if not isinstance(self.confidence, float):
            raise TypeError("Confidence must be a float")

        if not isinstance(self.output, dict):
            raise TypeError("Output must be a dict")

        return EngineResponse(
            name=self.name, confidence=self.confidence, data=self.output
        )

    @abstractmethod
    def prepare(self) -> bool:
        """Prepares the engine.

        Engine preparation is done during the preparation stage in the
        run.sh script. It is executed outside of the miner loop and
        should ensure that the miner does not have to perform
        unnecessary time or resource intensive operations during the
        startup process, such as downloading models or initializing
        databases.

        Returns:
            An instance of bool depicting whether the preparation was a
            success or a failure
        """

    @abstractmethod
    def initialize(self):
        """Initializes the engine.

        Engine initialization is done during the miner launch before
        starting the main loop. The purpose of the initialize() method
        is to return the objects used for the entire duration of the
        runtime. This can include objects such as persistent database
        connections, models, tokenizers or any data you want to persist
        throughout the engine executions.

        Return values are determined by the engine-specific
        implementation.
        """

    @abstractmethod
    def execute(self):
        """Executes the engine.

        This method is responsible for analyzing the input. It should
        contain all of the logic that is required to reach a conclusion
        about the input.

        This method must set the self.confidence and self.output
        instance attributes.

        Return values are determined by the engine-specific
        implementation.
        """
