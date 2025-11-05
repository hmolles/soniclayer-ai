def extract_segments(transcript_segments, classifier_results, persona_feedback_list=None):
    """
    Combine transcript segments with classifier output and persona scores.
    Flags repeated topics.
    
    Args:
        transcript_segments: List of segment dicts with 'text', 'start', 'end'
        classifier_results: List of classification dicts with 'topic' and 'tone'
        persona_feedback_list: List of dicts with persona keys (e.g., {'genz': {...}, 'advertiser': {...}})
    
    Returns:
        List of enriched segment dicts with all data merged
    """
    segments = []
    for i, segment in enumerate(transcript_segments):
        segment_data = {
            "start": round(segment["start"], 2),
            "end": round(segment["end"], 2),
            "transcript": segment["text"],
            "topic": classifier_results[i]["topic"],
            "tone": classifier_results[i]["tone"],
        }

        # Add persona feedback if available
        if persona_feedback_list and i < len(persona_feedback_list):
            persona_data = persona_feedback_list[i]
            
            # Add GenZ feedback
            if "genz" in persona_data:
                segment_data["genz"] = persona_data["genz"]
            
            # Add Advertiser feedback
            if "advertiser" in persona_data:
                segment_data["advertiser"] = persona_data["advertiser"]

        # Flag repeated topics
        if i > 0 and classifier_results[i]["topic"] == classifier_results[i - 1]["topic"]:
            segment_data["note"] = "Repeated theme"

        segments.append(segment_data)

    return segments