from core.models_groq import chat

def academic_qa(question: str, domain: str="general") -> str:
    system = f"You are a precise academic Q&A tutor for {domain}. Cite concepts, keep it concise."
    return chat(system, question, temperature=0.2)
