from typing import Dict, Any
from core.models_groq import chat

def study_plan(name: str, course: str, grade: str, goals: str, hours_per_week: int=6) -> str:
    system = "You design concise, actionable study plans."
    user = f"""
Student: {name}
Course: {course}
Current grade/level: {grade}
Goals: {goals}
Time available: {hours_per_week} hours/week

Produce:
- 4-week plan (weekly bullets)
- Daily micro-habits
- Recommended resources (free only)
- Risks & mitigation
Keep it compact and practical.
"""
    return chat(system, user, temperature=0.3)

def flashcards(topic: str, n: int=10) -> str:
    system = "You create compact flashcards as JSON."
    user = f"""
Create {n} flashcards for topic "{topic}".
Return JSON: {{"topic": "...", "cards":[{{"front":"", "back":""}}]}}
Keep the back short and factual. Only JSON.
"""
    return chat(system, user, json_mode=True)
