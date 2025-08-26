# modules/transcription.py
#
# Fast, free YouTube → Transcript:
# 1) Try official captions (manual/generated, en/en-US/en-GB)  → instant if available
# 2) Try timedtext HTTP fallback                              → still instant
# 3) Fallback: yt-dlp + faster-whisper                        → speed-optimized
#
# Env (set via .env or Streamlit Secrets):
#   FAST_WHISPER_MODEL=tiny.en     # tiny.en / base.en / small.en / base ...
#   FAST_WHISPER_COMPUTE=int8      # int8 (CPU), float16 (CUDA)
#   FAST_WHISPER_THREADS=4         # CPU threads (default: cpu_count-1)
#   FAST_WHISPER_WORKERS=1         # internal workers for chunk pipeline
#   USE_CUDA=0                     # 1 to use GPU if available
#   YT_COOKIES=/abs/path/to/cookies.txt  # OPTIONAL: Netscape-format cookies for age/region/member videos

from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import re, requests, os, tempfile
import xml.etree.ElementTree as ET
from typing import Optional

# --------------------- Utilities ---------------------

def _extract_video_id(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    m = re.search(r"(?:v=|/shorts/|/embed/|youtu\.be/)([0-9A-Za-z_-]{11})", url)
    if m:
        return m.group(1)
    if re.fullmatch(r"[0-9A-Za-z_-]{11}", url):
        return url
    m = re.search(r"[?&]v=([0-9A-Za-z_-]{11})", url)
    return m.group(1) if m else ""

def _timedtext_fallback(vid: str) -> Optional[str]:
    """
    Cheap HTTP fallback that tries YouTube's timedtext endpoints (manual or ASR).
    Returns plain concatenated text or None.
    """
    variants = [
        f"https://video.google.com/timedtext?lang=en&v={vid}",
        f"https://video.google.com/timedtext?lang=en-US&v={vid}",
        f"https://video.google.com/timedtext?lang=en&kind=asr&v={vid}",
        f"https://video.google.com/timedtext?lang=en-US&kind=asr&v={vid}",
    ]
    headers = {"User-Agent": "Mozilla/5.0"}  # reduce 403/429s
    for url in variants:
        try:
            r = requests.get(url, timeout=30, headers=headers)
            if r.status_code == 200 and r.text.strip():
                try:
                    root = ET.fromstring(r.text)
                except ET.ParseError:
                    continue
                texts = []
                for node in root.findall(".//text"):
                    txt = (node.text or "").strip()
                    if txt:
                        texts.append(txt)
                if texts:
                    return " ".join(texts)
        except requests.RequestException:
            continue
    return None

# --------------------- Fast Whisper (tuned) ---------------------

_WHISPER_MODEL = None  # singleton, loaded once

def _get_cache_dir() -> str:
    p = os.path.join(os.path.expanduser("~"), ".cache", "learnnext", "yt")
    os.makedirs(p, exist_ok=True)
    return p

def _find_cached_audio(vid: str) -> Optional[str]:
    cd = _get_cache_dir()
    for ext in (".webm", ".m4a", ".mp3", ".opus"):
        p = os.path.join(cd, vid + ext)
        if os.path.exists(p):
            return p
    return None

def _target_audio_template(vid: str) -> str:
    # yt-dlp will replace %(ext)s; we prefer webm/opus when possible
    return os.path.join(_get_cache_dir(), f"{vid}.%(ext)s")

def _get_whisper_model():
    """
    Load faster-whisper once and reuse. Tuned for speed (int8 on CPU by default).
    """
    global _WHISPER_MODEL
    if _WHISPER_MODEL is not None:
        return _WHISPER_MODEL
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except Exception:
        os.environ["YT_DEBUG_LAST"] = "faster_whisper_import_failed"
        return None

    model_size   = os.getenv("FAST_WHISPER_MODEL", "tiny.en")
    device       = "cuda" if os.getenv("USE_CUDA", "0") == "1" else "cpu"
    compute_type = "float16" if device == "cuda" else os.getenv("FAST_WHISPER_COMPUTE", "int8")

    # sensible default: use most CPU cores but leave 1 free
    try:
        default_threads = max(1, (os.cpu_count() or 2) - 1)
    except Exception:
        default_threads = 1
    cpu_threads = int(os.getenv("FAST_WHISPER_THREADS", str(default_threads)))

    try:
        _WHISPER_MODEL = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type,
            cpu_threads=cpu_threads,
        )
    except Exception as e:
        os.environ["YT_DEBUG_LAST"] = f"faster_whisper_init_error:{type(e).__name__}"
        return None
    return _WHISPER_MODEL

def _whisper_from_youtube(url: str, vid: str) -> Optional[str]:
    """
    Final robust fallback:
      1) Use cached audio if present; else download low-bitrate opus via yt-dlp.
      2) Transcribe with faster-whisper (greedy, language='en').
    Returns transcript text or None on failure.
    """
    try:
        import yt_dlp  # type: ignore
    except Exception:
        os.environ["YT_DEBUG_LAST"] = "yt_dlp_missing"
        return None  # optional dep not installed

    model = _get_whisper_model()
    if model is None:
        # YT_DEBUG_LAST set inside _get_whisper_model if failure
        return None

    # 1) try cache first
    path = _find_cached_audio(vid)

    # else download to cache
    if not path:
        outtmpl = _target_audio_template(vid)
        ydl_opts = {
            # Prefer small opus audio to speed up download + decode
            "format": "bestaudio[acodec=opus][abr<=64]/bestaudio[abr<=64]/bestaudio/best",
            "outtmpl": outtmpl,
            "quiet": True,
            "noplaylist": True,
            "nocheckcertificate": True,
            # optional cache dir for yt-dlp's own cookies/etc
            "cachedir": os.path.join(_get_cache_dir(), ".ytcache"),
        }

        cookies = os.getenv("YT_COOKIES")
        if cookies and os.path.exists(cookies):
            ydl_opts["cookiefile"] = cookies

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                guessed = ydl.prepare_filename(info)
                # normalize actual saved file (ext may differ)
                if os.path.exists(guessed):
                    path = guessed
                else:
                    base = os.path.splitext(guessed)[0]
                    for ext in (".webm", ".m4a", ".mp3", ".opus"):
                        candidate = base + ext
                        if os.path.exists(candidate):
                            path = candidate
                            break
        except Exception as e:
            os.environ["YT_DEBUG_LAST"] = f"yt_dlp_error:{type(e).__name__}"
            return None

    if not path or not os.path.exists(path):
        os.environ["YT_DEBUG_LAST"] = "audio_file_missing"
        return None

    # 2) transcribe (speed-tuned)
    try:
        # number of internal workers that process audio chunks
        try:
            num_workers = int(os.getenv("FAST_WHISPER_WORKERS", "1"))
        except Exception:
            num_workers = 1

        segments, _ = model.transcribe(
            path,
            language="en",                     # skip language detection
            vad_filter=True,                   # keep segments clean (minor cost)
            beam_size=1,                       # greedy decoding for speed
            temperature=0.0,                   # deterministic + fast
            condition_on_previous_text=False,  # small speed-up

        )
        text = " ".join(s.text.strip() for s in segments if getattr(s, "text", "").strip())
        return text.strip() or None
    except Exception as e:
        os.environ["YT_DEBUG_LAST"] = f"whisper_transcribe_error:{type(e).__name__}"
        return None

# --------------------- Public API ---------------------

def youtube_transcript(url: str) -> str:
    """
    Preferred order:
      1) Official transcript API (manual > generated; try en/en-US/en-GB; translate if needed)
      2) Timedtext HTTP fallback (free, no download)
      3) fast-whisper fallback (yt-dlp + faster-whisper, speed-optimized)
    """
    vid = _extract_video_id(url)
    if not vid:
        return "Invalid YouTube URL or video ID."

    # --- 1) Official transcripts ---
    try:
        srt = YouTubeTranscriptApi.get_transcript(vid, languages=["en", "en-US", "en-GB"])
        return " ".join([x["text"] for x in srt if x["text"].strip()])
    except NoTranscriptFound:
        try:
            transcripts = YouTubeTranscriptApi.list_transcripts(vid)

            # Prefer matching en transcript; otherwise try manual > generated
            try:
                t = transcripts.find_transcript(["en", "en-US", "en-GB"])
            except Exception:
                t = None
                if getattr(transcripts, "_manually_created_transcripts", {}):
                    t = transcripts.find_manually_created_transcript(
                        transcripts._manually_created_transcripts.keys()
                    )
                if t is None and getattr(transcripts, "_generated_transcripts", {}):
                    t = transcripts.find_generated_transcript(
                        transcripts._generated_transcripts.keys()
                    )

            if t is not None:
                if getattr(t, "language_code", "").startswith("en") is False:
                    try:
                        t = t.translate("en")
                    except Exception:
                        pass
                data = t.fetch()
                if data:
                    return " ".join([x["text"] for x in data if x["text"].strip()])
        except Exception as e:
            os.environ["YT_DEBUG_LAST"] = f"official_list_error:{type(e).__name__}"
    except TranscriptsDisabled:
        # allow fallbacks
        os.environ["YT_DEBUG_LAST"] = "transcripts_disabled"
    except Exception as e:
        os.environ["YT_DEBUG_LAST"] = f"official_api_error:{type(e).__name__}"

    # --- 2) Timedtext HTTP fallback ---
    tt = _timedtext_fallback(vid)
    if tt:
        return tt

    # --- 3) fast-whisper fallback (speed-optimized) ---
    wt = _whisper_from_youtube(url, vid)
    if wt:
        return wt

    hint = os.environ.get("YT_DEBUG_LAST", "unknown")
    return (
        "No transcript available. This can happen if captions are disabled, region-restricted, "
        "members-only/age-restricted, or due to temporary network/rate limits.\n"
        f"(debug: {hint})"
    )

# ---- Optional: preload model on module import (hides first-time load) ----
try:
    _ = _get_whisper_model()
except Exception:
    # If deps are missing in some envs, ignore; caption flow still works.
    pass
