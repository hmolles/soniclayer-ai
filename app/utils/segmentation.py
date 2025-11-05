def segment_transcript(transcript: str, segment_duration: float = 15.0) -> list:
    """
    Break transcript into segments based on estimated duration.
    Assumes ~2.5 words per second.
    """
    words = transcript.split()
    words_per_segment = int(segment_duration * 2.5)
    segments = []

    for i in range(0, len(words), words_per_segment):
        segment_text = " ".join(words[i:i + words_per_segment])
        start = round(i / 2.5, 2)
        end = round((i + words_per_segment) / 2.5, 2)
        segments.append({
            "start": start,
            "end": end,
            "text": segment_text
        })

    return segments