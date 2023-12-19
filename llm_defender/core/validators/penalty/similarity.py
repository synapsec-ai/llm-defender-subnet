import bittensor as bt
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np

# Sample documents
document_1 = "This is the first document"
document_2 = "This document is the second document"
document_3 = "And this is the third one"

# Create a CountVectorizer to convert text to word count vectors
vectorizer = CountVectorizer()

# Fit and transform the documents into vectors
vectorized_docs = vectorizer.fit_transform([document_1, document_2, document_3])

# Calculate cosine similarity between document_1 and document_2
cosine_sim = cosine_similarity(vectorized_docs[0], vectorized_docs[1])

print(f"Cosine Similarity between document_1 and document_2: {cosine_sim[0][0]}")


def _check_response_history(uid, miner_responses, engine, penalty_name="High-similarity score"):
    """Checks the response history to determine the similarity of engine responses"""
    # Isolate engine-specific data
    penalty = 0.0
    engine_data = [entry for item in miner_responses for entry in item.get('engine_data', []) if entry.get('name') == engine]
    if not engine_data:
        return penalty
    
    # Calculate duplicsate percentage
    engine_data_str = [str(entry["data"]) for entry in engine_data]

    # Create a CountVectorizer to convert text to word count vectors
    vectorizer = CountVectorizer()

    # Fit and transform the documents into vectors
    vectorized_docs = vectorizer.fit_transform(engine_data_str)

    # Calculate pairwise cosine similarity for all combinations of documents
    cosine_sim_matrix = cosine_similarity(vectorized_docs)

    # Exclude self-similarity values (diagonal) and compute average
    mask = np.triu(np.ones(cosine_sim_matrix.shape), k=1).astype(bool)
    similarities = cosine_sim_matrix[mask]

    if not similarities:
        return penalty
    
    average_similarity = similarities.mean()
    bt.logging.debug(f'Average similarity: {average_similarity}')
    
    if average_similarity > 0.9:
        penalty += 3
    elif average_similarity > 0.8:
        penalty += 2
    elif average_similarity > 0.7:
        penalty += 1
    elif average_similarity > 0.6:
        penalty += 0.5

    bt.logging.debug(f"Applied penalty score '{penalty}' from rule '{penalty_name}' for UID: '{uid}' for engine: '{engine}'. Average confidence: '{average_similarity}'")
    return penalty

def check_penalty(uid, miner_responses, response):
    """This function checks the total penalty score within similarity
    category"""
    
    penalty = 0.0
    for engine in ["engine:text_classification", "engine:yara", "engine:vector_search"]:
        penalty += _check_response_history(uid, miner_responses, engine)

    return penalty