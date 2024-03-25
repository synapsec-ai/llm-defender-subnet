import pytest
from unittest.mock import MagicMock, patch
from llm_defender.core.validators.analyzers.prompt_injection.reward.vector_search import VectorSearchValidation


@pytest.fixture
def mock_sentence_transformer():
    mock_model = MagicMock()
    mock_model.encode = MagicMock(return_value=[[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    return mock_model


@pytest.fixture
def mock_sklearn_dependencies():
    with patch(
            "llm_defender.core.validators.analyzers.prompt_injection.reward.vector_search.cosine_distances") as mock_cosine_distances, \
            patch(
                "llm_defender.core.validators.analyzers.prompt_injection.reward.vector_search.pairwise_distances") as mock_pairwise_distances, \
            patch(
                "llm_defender.core.validators.analyzers.prompt_injection.reward.vector_search.linear_kernel") as mock_linear_kernel:
        mock_cosine_distances.return_value = [[0.1, 0.2], [0.3, 0.4]]
        mock_pairwise_distances.return_value = [[0.1, 0.2], [0.3, 0.4]]
        mock_linear_kernel.return_value = [[0.1, 0.2], [0.3, 0.4]]
        yield mock_cosine_distances, mock_pairwise_distances, mock_linear_kernel


def test_calculate_correlation():
    validation = VectorSearchValidation()
    confidences = [0.8, 0.6]
    distances = [[0.1, 0.2], [0.3, 0.4]]
    correlation = validation.calculate_correlation(confidences, distances)
    assert isinstance(correlation, float)  # Correlation value is float


def test_calculate_difference():
    validation = VectorSearchValidation()
    actual_distances = [0.2, 0.4]
    calculated_distances = [0.1, 0.3]
    difference = validation.calculate_difference(actual_distances, calculated_distances)
    assert isinstance(difference, float)  # Difference value is float
