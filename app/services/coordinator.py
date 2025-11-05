def aggregate_scores(persona_scores: list) -> dict:
    weights = {
        "genz": 1.0,
        "parents": 1.2,
        "regional": 1.0,
        "advertiser": 1.5,
        "academic": 1.0
    }

    weighted_sum = sum(score * weights.get(name, 1.0) for name, score in persona_scores.items())
    total_weight = sum(weights.get(name, 1.0) for name in persona_scores.keys())

    consensus = round(weighted_sum / total_weight, 2)

    return {
        "consensus_rating": consensus,
        "weighted_scores": persona_scores
    }