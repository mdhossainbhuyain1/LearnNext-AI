# LearnNext AI

A Streamlit app that blends Groq LLM + Hugging Face Inference API to deliver:
- Personalized Learning
- Real-time Academic Q&A
- Summarization (text + YouTube + Documents)
- Document Processing (PDF, DOCX, TXT)
- Coding Mentor
- Wellness (Sentiment + Emotions)
- Quiz + Flashcards
- Clean blue/frozi UI

## Quickstart
1) `pip install -r requirements.txt`
2) Copy `.env.example` to `.env` and fill keys
3) `streamlit run app.py`

**Note**: Document processing requires `PyPDF2` and `python-docx` packages (included in requirements.txt)

## Keys
- Get a **Groq API** key: https://console.groq.com
- Get a **Hugging Face Inference API** key: https://huggingface.co/settings/tokens

## Notes
- We **do not** download local models by default. HF Inference API hosts summarization/sentiment/emotions models.
- Transcripts use **YouTubeTranscriptAPI** (no key). Optional local audio → `faster-whisper` (CPU) if you install it.

## No Dummy Data
- All analytics are computed from real user interactions during your session; nothing is faked.
