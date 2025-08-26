import streamlit as st
from core.utils import inject_css
from core.sidebar import render_sidebar
render_sidebar("About")

st.set_page_config(page_title="About", page_icon="ℹ️", layout="wide")
inject_css()
st.markdown('<div class="app-title pop">About LearnNext AI</div>', unsafe_allow_html=True)

st.markdown("""
<div class="card pop">
  <h3>✨ Features</h3>
  <ul>
    <li><b>Personalized Learning:</b> weekly plan, micro-habits</li>
    <li><b>Academic Q&A:</b> Groq Llama 3.1 8B Instruct</li>
    <li><b>Summarization:</b> DistilBART</li>
    <li><b>Transcripts:</b> YouTubeTranscriptAPI </li>
    <li><b>Coding Mentor:</b> reviews, debugging, concept explainers</li>
    <li><b>Wellness:</b> sentiment + emotions with supportive tips</li>
    <li><b>Quiz & Flashcards:</b> MCQs with animated feedback</li>
    <li><b>No Dummy Data:</b> usage metrics update only when YOU interact</li>
  </ul>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="card pop" style="margin-top:12px">
  <h3>🔧 Tech</h3>
    <span class="pill">Python</span>
    <span class="pill">Streamlit</span>
    <span class="pill">Groq</span>
    <span class="pill">Hugging Face</span>
 
</div>
""", unsafe_allow_html=True)
