import json, os, time, re
import streamlit as st
from pathlib import Path
from typing import Any, Dict, List
from .config import PALETTE

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
LOG_FILE = DATA_DIR / "analytics.json"

def inject_css():
    st.markdown(f"""
    <style>
      .app-title {{
        font-weight: 800;
        font-size: 2.0rem;
        background: linear-gradient(90deg, #3fb7ff, {PALETTE['accent']});
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
      }}
      .subtle {{
        color:{PALETTE['muted']};
        font-size: 0.95rem;
      }}
      .card {{
        background:{PALETTE['panel']};
        padding:1rem 1.25rem;
        border-radius:18px;
        box-shadow:0 4px 24px rgba(0,0,0,0.25);
        border:1px solid rgba(255,255,255,0.06);
      }}
      .pill {{
        display:inline-block;
        padding:4px 10px;
        border-radius:999px;
        background:rgba(0,194,209,0.12);
        border:1px solid rgba(0,194,209,0.45);
        color:{PALETTE['text']};
        font-size:0.8rem;
        margin-right:6px;
      }}
      @keyframes pop {{
        0% {{ transform:scale(0.98); opacity:.8; }}
        60% {{ transform:scale(1.02); opacity:1; }}
        100% {{ transform:scale(1); }}
      }}
      .pop {{
        animation: pop .6s ease;
      }}
      /* Quiz animations */
      .correct {{
        background: rgba(0,214,143,.12) !important;
        border: 1px solid rgba(0,214,143,.45) !important;
      }}
      .incorrect {{
        background: rgba(255,77,79,.12) !important;
        border: 1px solid rgba(255,77,79,.45) !important;
      }}
    </style>
    """, unsafe_allow_html=True)

def _load_log() -> Dict[str, Any]:
    if LOG_FILE.exists():
        try:
            return json.loads(LOG_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def _save_log(obj: Dict[str, Any]):
    LOG_FILE.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

def record_event(event_type: str, payload: Dict[str, Any]):
    log = _load_log()
    ts = str(int(time.time()))
    log[ts] = {"event": event_type, "payload": payload}
    _save_log(log)

def get_usage_counts():
    log = _load_log()
    stats = {"qna":0, "coding":0, "summaries":0, "transcripts":0, "wellness":0, "quiz":0}
    for _, v in log.items():
        e = v.get("event")
        if e in stats: stats[e]+=1
    return stats, len(log)

def parse_json_maybe(s: str):
    try:
        return json.loads(s)
    except Exception:
        # try to extract json
        match = re.search(r"\{.*\}|\[.*\]", s, flags=re.S)
        if match:
            try: return json.loads(match.group(0))
            except Exception: return None
        return None
