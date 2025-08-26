import requests, time
from typing import Dict, Any
from .config import HF_API_KEY, HF_SUMMARIZATION_MODEL, HF_SENTIMENT_MODEL, HF_EMOTION_MODEL, HF_TIMEOUT_SEC

def _hf_request(model_id: str, payload: Dict[str, Any], timeout=None) -> Any:
    if not HF_API_KEY:
        raise RuntimeError("HF_API_KEY is missing. Put it in .env")
    url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    to = int(timeout or HF_TIMEOUT_SEC)

    r = requests.post(url, headers=headers, json=payload, timeout=to)

    # If model is cold/loading, retry once
    if r.status_code == 503 and "loading" in r.text.lower():
        time.sleep(2)
        r = requests.post(url, headers=headers, json=payload, timeout=to)

    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        try:
            err = r.json()
        except Exception:
            err = {"error": r.text}
        raise RuntimeError(f"HuggingFace API error for '{model_id}': {err.get('error', str(e))}") from e

    return r.json()

def summarize_text(text: str, max_len: int = 200, min_len: int = 50, min_length: int | None = None) -> str:
    if min_length is not None:
        min_len = int(min_length)
    out = _hf_request(HF_SUMMARIZATION_MODEL, {
        "inputs": text,
        "parameters": {"max_length": int(max_len), "min_length": int(min_len), "do_sample": False}
    })
    if isinstance(out, list) and out and isinstance(out[0], dict) and "summary_text" in out[0]:
        return out[0]["summary_text"]
    if isinstance(out, dict) and "generated_text" in out:
        return out["generated_text"]
    return str(out)

def _unwrap_items(out):
    """HF outputs can be [{...}, ...] or [[{...}, ...]]. Return a flat list of dicts."""
    if isinstance(out, list) and out:
        return out[0] if isinstance(out[0], list) else out
    return []

def sentiment(text: str) -> Dict[str, float]:
    out = _hf_request(HF_SENTIMENT_MODEL, {"inputs": text})
    items = _unwrap_items(out)
    scores: Dict[str, float] = {}
    for d in items:
        if isinstance(d, dict) and "label" in d and "score" in d:
            scores[d["label"].lower()] = float(d["score"])
    return scores

def emotions(text: str) -> Dict[str, float]:
    out = _hf_request(HF_EMOTION_MODEL, {"inputs": text, "parameters": {"return_all_scores": True}})
    items = _unwrap_items(out)
    emo: Dict[str, float] = {}
    for d in items:
        if isinstance(d, dict) and "label" in d and "score" in d:
            emo[d["label"].lower()] = float(d["score"])
    return emo
