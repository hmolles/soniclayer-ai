class PersonaAgent:
    def __init__(self, name: str, description: str, preferences: dict, rubric: dict):
        self.name = name
        self.description = description
        self.preferences = preferences
        self.rubric = rubric

    def evaluate(self, segment: dict) -> dict:
        topic = segment.get("topic", "")
        tone = segment.get("tone", "")
        transcript = segment.get("transcript", "")
        tags = segment.get("tags", [])

        score = self.score_segment(topic, tone, transcript, tags)
        confidence = self.estimate_confidence(score)
        rationale = self.generate_rationale(score, topic, tone, transcript)
        opinion = self.generate_opinion(score, topic, tone)
        note = self.generate_note(topic, tone, tags)

        return {
            "score": score,
            "confidence": confidence,
            "opinion": opinion,
            "note": note,
            "rationale": rationale
        }

    def score_segment(self, topic: str, tone: str, transcript: str, tags: list) -> int:
        score = 3  # Default neutral score
        if tone.lower() in self.preferences.get("preferred_tones", []):
            score += 1
        if topic.lower() in self.preferences.get("preferred_topics", []):
            score += 1
        if any(tag in self.preferences.get("disliked_tags", []) for tag in tags):
            score -= 2
        return max(1, min(score, 5))

    def estimate_confidence(self, score: int) -> float:
        return round(0.5 + (abs(score - 3) / 4), 2)

    def generate_rationale(self, score: int, topic: str, tone: str, transcript: str) -> str:
        return (
            f"Rated {score} because the segment was '{tone}', "
            f"covered the topic '{topic}', and matched the persona's preferences."
        )

    def generate_opinion(self, score: int, topic: str, tone: str) -> str:
        if score >= 4:
            return f"Engaging and well-targeted segment on {topic} with a {tone} tone."
        elif score == 3:
            return f"Acceptable segment on {topic}, but could be more engaging."
        else:
            return f"Segment on {topic} felt misaligned with expected tone ({tone})."

    def generate_note(self, topic: str, tone: str, tags: list) -> str:
        if "repetition" in tags:
            return "Repeated theme from previous segment."
        if "profanity" in tags:
            return "Contains potentially offensive language."
        return ""

    def get_prompt(self, segment: dict) -> str:
        context = segment.get("context", "")
        return f"""
You are {self.description}.
Evaluate the following radio programme segment.

Transcript:
{segment.get("transcript", "")}

Topic: {segment.get("topic", "")}
Tone: {segment.get("tone", "")}
Tags: {', '.join(segment.get("tags", []))}

Instructions:
- Rate the segment from 1 to 5 based on relevance, tone fit, engagement, and cultural alignment.
- Provide a one-sentence opinion.
- Include a rationale and optional note if needed.
"""

    def parse_llm_response(self, response: str) -> dict:
        lines = response.strip().split("\n")
        result = {
            "score": int(lines[0].split(":")[1].strip()) if "Rating:" in lines[0] else 3,
            "opinion": lines[1].split(":")[1].strip() if len(lines) > 1 else "",
            "note": lines[2].split(":")[1].strip() if len(lines) > 2 else "",
            "rationale": lines[3].split(":")[1].strip() if len(lines) > 3 else ""
        }
        result["confidence"] = self.estimate_confidence(result["score"])
        return result