import math
import streamlit as st
from core.utils import inject_css, record_event
from modules.transcription import youtube_transcript
from modules.summarizer import summarize_any, extract_text_from_file
from core.sidebar import render_sidebar
render_sidebar("Lectures & Summarizers")

st.set_page_config(page_title="YouTube & Summarizers", page_icon="🎧", layout="wide")
inject_css()

# ------------------------- Header (same template as others) -------------------------
st.markdown("""
<div class="card pop" style="padding:22px;
  background: linear-gradient(135deg, rgba(15,26,48,.95) 0%, rgba(11,18,32,.95) 60%, rgba(0,194,209,.18) 120%);
  border:1px solid rgba(0,194,209,.35);">
  <div style="display:flex;align-items:center;justify-content:space-between;gap:18px;flex-wrap:wrap;">
    <div>
      <div class="app-title" style="margin-bottom:6px;">Lectures & Summarizers</div>
      <div class="subtle">YouTube transcript + fast summarizers (Smart chunking handles long inputs)</div>
    </div>
    <div style="min-width:240px;height:88px;border-radius:16px;
                background: radial-gradient(70px 70px at 80% 40%, rgba(0,194,209,.55), transparent 60%),
                            linear-gradient(135deg,#0b1220 0%,#0f1a30 60%,rgba(0,194,209,.65) 135%);
                box-shadow:0 10px 28px rgba(0,0,0,.35);">
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ----------------------------- Helpers -----------------------------
def _reading_time(text: str) -> str:
    words = max(1, len((text or "").split()))
    minutes = words / 200.0
    return f"~{max(1, round(minutes))} min read · {words} words"

def _smart_summarize(text: str, min_len: int, max_len: int) -> str:
    """
    Map-reduce style: chunk long texts to avoid model limits, then summarize the summaries.
    Uses summarize_any() under the hood (HF Inference API).
    """
    text = (text or "").strip()
    if not text:
        return "Please provide text to summarize."
    if len(text) <= 3500:
        return summarize_any(text, min_len=min_len, max_len=max_len)

    chunks, acc = [], []
    acc_len = 0
    for sent in text.replace("\n", " ").split(". "):
        s = (sent + ("" if sent.endswith(".") else "."))  # re-append period
        if acc_len + len(s) > 3000 and acc:
            chunks.append(" ".join(acc))
            acc, acc_len = [], 0
        acc.append(s)
        acc_len += len(s)
    if acc:
        chunks.append(" ".join(acc))

    partials = []
    for i, ch in enumerate(chunks, 1):
        with st.spinner(f"Summarizing part {i}/{len(chunks)}..."):
            partials.append(summarize_any(ch, min_len=min_len, max_len=max_len))

    stitched = " ".join(partials)
    with st.spinner("Creating final concise summary..."):
        return summarize_any(stitched, min_len=min_len, max_len=max_len)

def _stat_chip(label: str):
    st.markdown(f"""<span class="pill" style="margin-bottom:4px;display:inline-block">{label}</span>""",
                unsafe_allow_html=True)

def _section_header(title: str, emoji: str):
    st.markdown(f"""
    <div class="card pop" style="
        padding:18px;
        background: linear-gradient(135deg, rgba(15,26,48,.95) 0%, rgba(11,18,32,.95) 60%, rgba(0,194,209,.18) 120%);
        border:1px solid rgba(0,194,209,.35); margin-bottom:12px;">
      <div style="display:flex;align-items:center;gap:10px;">
        <div style="font-size:1.4rem">{emoji}</div>
        <div style="font-weight:700">{title}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------- Tabs -----------------------------
tab1, tab2, tab3 = st.tabs([
    "🎥 YouTube Video Summarizer",
    "📄 Doc Summarizer (PDF/DOCX/TXT)",
    "📝 Long Text Summarizer"
])

# =================================================================
# Tab 1: YouTube video summarizer
# =================================================================
with tab1:
    _section_header("YouTube → Transcript → Summary", "🎥")
    url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=XXXXXXXXXXX")

    with st.expander("Summary options", expanded=False):
        c1, c2 = st.columns(2)
        min_len = c1.slider("Min summary length", 20, 250, 50)
        max_len = c2.slider("Max summary length", 60, 600, 220)
        style = st.selectbox("Style (post-formatting)", ["Paragraph", "Bullet points"], index=0,
                             help="Formatting only; content still comes from the model output.")

    go = st.button("Fetch Transcript & Summarize", key="yt_sum", type="primary", use_container_width=True)

    if go:
        if not url.strip():
            st.warning("Please paste a YouTube URL.")
        else:
            with st.spinner("Fetching transcript..."):
                t = youtube_transcript(url)
            st.text_area("Transcript", t, height=220)
            if t and not t.lower().startswith(("invalid", "no transcript", "could not", "transcripts are disabled")):
                _stat_chip(_reading_time(t))
                record_event("transcripts", {"source": "youtube", "len": len(t)})

                with st.spinner("Summarizing…"):
                    s = _smart_summarize(t, min_len=min_len, max_len=max_len)

                if style == "Bullet points":
                    bullets = [f"- {x.strip()}" for x in s.split(". ") if x.strip()]
                    s = "\n".join(bullets)

                st.markdown("### Summary")
                st.markdown(f"""
                <div class="card pop" style="border-left: 4px solid rgba(0,194,209,.65);">
                  <div style="line-height:1.6;white-space:pre-wrap">{s}</div>
                </div>
                """, unsafe_allow_html=True)

                colA, colB = st.columns(2)
                colA.download_button("Download summary (.txt)", s, file_name="video_summary.txt", mime="text/plain",
                                     use_container_width=True)
                colB.download_button("Download transcript (.txt)", t, file_name="video_transcript.txt", mime="text/plain",
                                     use_container_width=True)

                record_event("summaries", {"chars": len(t), "source": "youtube"})
                st.balloons()
            else:
                st.error(t or "Could not fetch transcript.")

# =================================================================
# Tab 2: Document summarizer
# =================================================================
with tab2:
    _section_header("Summarize a document", "📄")

    f = st.file_uploader("Upload file", type=["pdf", "docx", "txt"])
    with st.expander("Summary options", expanded=False):
        c1, c2 = st.columns(2)
        min_len2 = c1.slider("Min summary length", 20, 250, 60, key="dmin")
        max_len2 = c2.slider("Max summary length", 60, 600, 240, key="dmax")
        style2 = st.selectbox("Style (post-formatting)", ["Paragraph", "Bullet points"], index=0, key="dsty")

    if st.button("Summarize Document", type="primary", use_container_width=True):
        if not f:
            st.warning("Please upload a file.")
        else:
            with st.spinner("Extracting text…"):
                text = extract_text_from_file(f)
            if not text or text.startswith(("Unsupported", "Error")):
                st.error(text if text else "Could not read file.")
            else:
                _stat_chip(_reading_time(text))
                st.text_area("Extracted text (preview)", text[:4000], height=220)

                with st.spinner("Summarizing…"):
                    s = _smart_summarize(text, min_len=min_len2, max_len=max_len2)

                if style2 == "Bullet points":
                    bullets = [f"- {x.strip()}" for x in s.split(". ") if x.strip()]
                    s = "\n".join(bullets)

                st.markdown("### Summary")
                st.markdown(f"""
                <div class="card pop" style="border-left: 4px solid rgba(0,194,209,.65);">
                  <div style="line-height:1.6;white-space:pre-wrap">{s}</div>
                </div>
                """, unsafe_allow_html=True)

                st.download_button("Download summary (.txt)", s, file_name="document_summary.txt", mime="text/plain",
                                   use_container_width=True)
                record_event("summaries", {"doc": getattr(f, "name", "uploaded_file"), "chars": len(text)})
                st.balloons()

# =================================================================
# Tab 3: Long text summarizer
# =================================================================
with tab3:
    _section_header("Summarize long text", "📝")

    tlong = st.text_area("Paste text to summarize", height=220)
    with st.expander("Summary options", expanded=False):
        c1, c2 = st.columns(2)
        min_len3 = c1.slider("Min summary length", 20, 250, 50, key="tmin")
        max_len3 = c2.slider("Max summary length", 60, 600, 220, key="tmax")
        style3 = st.selectbox("Style (post-formatting)", ["Paragraph", "Bullet points"], index=0, key="tsty")

    if st.button("Summarize", key="long_sum", type="primary", use_container_width=True):
        if not tlong.strip():
            st.warning("Please paste some text.")
        else:
            _stat_chip(_reading_time(tlong))
            with st.spinner("Summarizing…"):
                s = _smart_summarize(tlong, min_len=min_len3, max_len=max_len3)

            if style3 == "Bullet points":
                bullets = [f"- {x.strip()}" for x in s.split(". ") if x.strip()]
                s = "\n".join(bullets)

            st.markdown("### Summary")
            st.markdown(f"""
            <div class="card pop" style="border-left: 4px solid rgba(0,194,209,.65);">
              <div style="line-height:1.6;white-space:pre-wrap">{s}</div>
            </div>
            """, unsafe_allow_html=True)

            st.download_button("Download summary (.txt)", s, file_name="text_summary.txt", mime="text/plain",
                               use_container_width=True)
            record_event("summaries", {"chars": len(tlong)})
            st.balloons()
