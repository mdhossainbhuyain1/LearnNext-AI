from typing import Dict, Any
from core.models_hf import sentiment, emotions

def wellness_analysis(text: str) -> Dict[str, Any]:
    sent = sentiment(text)
    emo = emotions(text)
    # pick top emotion
    top_emotion = None
    if emo:
        top_emotion = max(emo.items(), key=lambda kv: kv[1])[0]
    tips = []
    if top_emotion in {"anxiety","fear","sadness","grief","nervousness"}:
        tips = [
            "Try 4-7-8 breathing for 1 minute.",
            "Write 3 worries, then 3 actions you can take.",
            "Take a brief walk and hydrate.",
        ]
    elif top_emotion in {"joy","approval","gratitude","pride"}:
        tips = [
            "Note what worked and plan to repeat it.",
            "Share your win with a friend.",
            "Set a tiny goal for tomorrow.",
        ]
    else:
        tips = [
            "Do a 5-minute stretch break.",
            "Message someone you trust.",
            "List one thing you can control today."
        ]
    return {"sentiment": sent, "emotions": emo, "top_emotion": top_emotion, "tips": tips}

DISCLAIMER = (
    "This assistant offers general well-being guidance and is not a substitute for professional care. "
    "If you feel unsafe or in crisis, please seek local emergency help immediately."
)
