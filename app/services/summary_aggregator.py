import json
import logging
from typing import List, Dict
from app.services.cache import redis_conn

logger = logging.getLogger(__name__)


def compute_score_distribution(scores: List[int]) -> Dict[str, int]:
    """
    Count occurrences of each score (1-5)
    
    Args:
        scores: List of integer scores [3, 4, 2, 5, 4, ...]
    
    Returns:
        {"1": 2, "2": 5, "3": 8, "4": 2, "5": 1}
    """
    distribution = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
    
    for score in scores:
        score_str = str(score)
        if score_str in distribution:
            distribution[score_str] += 1
    
    return distribution


def get_top_n_segments(scores: List[int], n: int = 3) -> List[int]:
    """
    Return indices of top N highest-scoring segments
    
    Args:
        scores: [2, 4, 3, 5, 1, 5, 3]
        n: number of top segments to return
    
    Returns:
        [3, 5, 1]  # Segment indices with highest scores
    """
    if not scores:
        return []
    
    indexed_scores = [(idx, score) for idx, score in enumerate(scores)]
    
    sorted_scores = sorted(indexed_scores, key=lambda x: x[1], reverse=True)
    
    top_n = sorted_scores[:n]
    
    return [idx for idx, score in top_n]


def get_worst_n_segments(scores: List[int], n: int = 2) -> List[int]:
    """
    Return indices of worst N lowest-scoring segments
    
    Args:
        scores: [2, 4, 3, 5, 1, 5, 3]
        n: number of worst segments to return
    
    Returns:
        [4, 0]  # Segment indices with lowest scores
    """
    if not scores:
        return []
    
    indexed_scores = [(idx, score) for idx, score in enumerate(scores)]
    
    sorted_scores = sorted(indexed_scores, key=lambda x: x[1])
    
    worst_n = sorted_scores[:n]
    
    return [idx for idx, score in worst_n]


def aggregate_persona_feedback(audio_id: str, persona_id: str, num_segments: int) -> Dict:
    """
    Aggregate all segment-level feedback for a single persona
    
    Fetch from Redis: persona_feedback:{persona_id}:{audio_id}:{segment_id}
    for segment_id in range(0, num_segments)
    
    Returns:
        {
            "avg_score": 3.2,
            "score_distribution": {"1": 1, "2": 3, "3": 5, "4": 6, "5": 3},
            "avg_confidence": 0.75,
            "top_segments": [5, 12, 7],
            "worst_segments": [2, 9]
        }
    """
    scores = []
    confidences = []
    
    for segment_id in range(num_segments):
        redis_key = f"persona_feedback:{persona_id}:{audio_id}:{segment_id}"
        
        try:
            feedback_data = redis_conn.get(redis_key)
            
            if feedback_data:
                feedback = json.loads(feedback_data)
                
                if "score" in feedback:
                    scores.append(feedback["score"])
                
                if "confidence" in feedback:
                    confidences.append(feedback["confidence"])
        
        except Exception as e:
            logger.warning(f"Error fetching feedback for {redis_key}: {e}")
            continue
    
    if not scores:
        return {
            "avg_score": 0,
            "score_distribution": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0},
            "avg_confidence": 0,
            "top_segments": [],
            "worst_segments": []
        }
    
    avg_score = round(sum(scores) / len(scores), 1)
    avg_confidence = round(sum(confidences) / len(confidences), 2) if confidences else 0
    distribution = compute_score_distribution(scores)
    top_segments = get_top_n_segments(scores, n=3)
    worst_segments = get_worst_n_segments(scores, n=2)
    
    return {
        "avg_score": avg_score,
        "score_distribution": distribution,
        "avg_confidence": avg_confidence,
        "top_segments": top_segments,
        "worst_segments": worst_segments
    }
