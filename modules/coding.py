from core.models_groq import chat

def code_review(code: str, lang: str="python") -> str:
    system = "You are a senior code reviewer. Provide specific, safe improvements and explain why."
    user = f"Language: {lang}\nCode:\n{code}\n\nReturn: issues, fixes, and improved snippet if applicable."
    return chat(system, user, temperature=0.2)

def debug_help(error: str, snippet: str="", lang: str="python") -> str:
    system = "You are a debugging assistant. Diagnose root causes and propose fixes."
    user = f"Language: {lang}\nError:\n{error}\nSnippet:\n{snippet}"
    return chat(system, user, temperature=0.2)

def concept_explain(concept: str, lang: str="python") -> str:
    system = "Explain programming concepts with short examples and clarity."
    return chat(system, concept, temperature=0.2)
