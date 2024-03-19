from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_distances
from sklearn.metrics import pairwise_distances
from sklearn.metrics.pairwise import linear_kernel
import numpy as np
from scipy.stats import spearmanr

class VectorSearchValidation:
    """Validation class for Vector Search"""
    def __init__(self, model = None):
        if model:
            self.model = self._load_model(model)
        else:
            self.model = model
    
    def _load_model(self, model):
        """Loads the model used to generate embeddings"""
        model = SentenceTransformer(model)

        return model

    def generate_embeddings(self, prompt, documents):
        """Generates embeddings for the given prompt and documents"""
        embeddings = self.model.encode([prompt] + documents, batch_size=32)
        
        return embeddings

    def _calculate_cosine(self, embeddings):
        """Calculates cosine distances"""
        distances = cosine_distances(embeddings[0].reshape(1, -1), embeddings[1:])

        return distances
    
    def _calculate_l2(self, embeddings):
        """Calculates l2 squared distances"""
        distances = pairwise_distances(embeddings[0:1], embeddings[1:], metric='euclidean', squared=True)
        
        return distances

    def _calculate_ip(self, embeddings):
        """Calculates inner product distance"""
        distances = 1.0 - np.dot(embeddings[0].reshape(1, -1), embeddings[1:].T)

        return distances

    def calculate_distance(self, embeddings, distance_function):
        """Calculates distance given the embeddings and the distance
        function
        """
        
        distances = []
        
        if distance_function == "cosine":
            calculated_distances = self._calculate_cosine(embeddings)
            for _, dist in enumerate(calculated_distances[0], start=1):
                distances.append(dist)
            return distances
        
        elif distance_function == "l2":
            calculated_distances = self._calculate_l2(embeddings)
            for _, dist in enumerate(calculated_distances[0], start=1):
                distances.append(dist)
            return distances
        
        elif distance_function == "ip":
            calculated_distances = self._calculate_ip(embeddings)
            for _, dist in enumerate(calculated_distances[0], start=1):
                distances.append(dist)
            return distances
        
        return False

    def calculate_correlation(self, confidences, distances):
        """Calculates spearman's rank correlation coefficient for miner
        response distances and confidences"""

        if not isinstance(confidences, list) or isinstance(confidences, bool):
            return False
        if not isinstance(distances, list) or isinstance(distances, bool):
            return False
        
        # Min distance is the one the matters in determining the confidence score
        min_distances = [min(entry) for entry in distances]

        # If all values in either list are the same, we cannot calculate correlation and results are invalid
        if all(x == min_distances[0] for x in min_distances) or all(x == confidences[0] for x in confidences):
            return 0.0
        
        correlation,_ = spearmanr(confidences, min_distances)

        if np.isnan(correlation):
            return 0.0

        return correlation

    def calculate_difference(self, actual_distances, calculated_distances):
        """Calculates distance of distances A and B"""

        if not isinstance(actual_distances, list) or isinstance(actual_distances, bool):
            return False
        if not isinstance(calculated_distances, list) or isinstance(calculated_distances, bool):
            return False
        if len(actual_distances) != len(calculated_distances):
            return False
        
        difference = [a - b for a, b in zip(actual_distances, calculated_distances)]

        return sum(difference)


     