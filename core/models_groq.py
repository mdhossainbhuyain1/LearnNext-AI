from typing import Optional, List, Dict, Any
from groq import Groq
from .config import GROQ_API_KEY, GROQ_MODEL

_client: Optional[Groq] = None

def _get_client() -> Groq:
    global _client
    if _client is None:
        if not GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is missing. Put it in .env")
        _client = Groq(api_key=GROQ_API_KEY)
    return _client

def chat(system_prompt: str, user_prompt: str, json_mode: bool=False, temperature: float=0.2) -> str:
    client = _get_client()
    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        temperature=temperature,
        messages=[
            {"role":"system", "content": system_prompt},
            {"role":"user", "content": user_prompt}
        ],
        response_format={"type":"json_object"} if json_mode else None
    )
    return resp.choices[0].message.content

def generate_quiz(topic: str, n_questions: int=5, difficulty: str="easy") -> Dict[str, Any]:
    system = "You are a strict quiz generator. Always return valid JSON exactly matching the schema."
    user = f"""
Create a multiple-choice quiz on "{topic}" with {n_questions} questions (difficulty: {difficulty}).
Schema:
{{
  "topic": "string",
  "questions":[
     {{
       "q":"string",
       "choices":["A","B","C","D"],
       "answer_index": 0,
       "explanation": "string"
     }}
  ]
}}
Rules:
- Choices must be plausible and unique
- The correct answer_index must be 0..3
- Explanations must be short and factual
Return only JSON.
"""
    out = chat(system, user, json_mode=True)
    return out
