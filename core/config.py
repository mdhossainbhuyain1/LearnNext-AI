import os
from dotenv import load_dotenv

load_dotenv()

# Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
HF_API_KEY   = os.getenv("HF_API_KEY", "").strip()

# Models
GROQ_MODEL              = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip()
HF_SUMMARIZATION_MODEL  = os.getenv("HF_SUMMARIZATION_MODEL", "sshleifer/distilbart-cnn-12-6").strip()
HF_SENTIMENT_MODEL      = os.getenv("HF_SENTIMENT_MODEL", "distilbert-base-uncased-finetuned-sst-2-english").strip()
HF_EMOTION_MODEL        = os.getenv("HF_EMOTION_MODEL", "j-hartmann/emotion-english-distilroberta-base").strip()
HF_TIMEOUT_SEC          = float(os.getenv("HF_TIMEOUT_SEC", "25"))

# UI palette
PALETTE = {
    "bg": "#0b1220",
    "panel": "#0f1a30",
    "accent": "#00c2d1",  # frozi
    "text": "#e6f7ff",
    "muted": "#9fdbe3",
    "ok": "#00d68f",
    "warn": "#ffd166",
    "bad": "#ff4d4f",
}
