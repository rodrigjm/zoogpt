"""
🐘 Zoocari the Elephant - Zoo Q&A Chatbot for Kids
A hallucination-free chatbot for children ages 6-12

Features:
- Friendly elephant character persona
- Age-appropriate language and content
- Strictly grounded responses (no hallucinations)
- 3 follow-up questions per response
- Kid-friendly Streamlit UI with Leesburg Animal Park branding
"""

import streamlit as st
import lancedb
import io
import os
import time
import uuid
from pathlib import Path
from openai import OpenAI
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv
from utils.text import strip_markdown, sanitize_html, load_css_file
from session_manager import (
    get_or_create_session,
    save_message,
    get_chat_history,
    get_session_stats
)

# ============================================================
# LOGGING UTILITIES
# ============================================================

def log(stage: str, message: str, level: str = "INFO"):
    """Print timestamped log message to console."""
    import sys
    timestamp = time.strftime("%H:%M:%S")
    emoji = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌", "TTS": "🔊", "STT": "🎤", "LLM": "🤖", "DB": "🗄️"}.get(level, "•")
    print(f"[{timestamp}] {emoji} [{stage}] {message}", flush=True)
    sys.stdout.flush()

# Local TTS (Kokoro)
try:
    from tts_kokoro import generate_speech_kokoro, is_kokoro_available, VOICE_PRESETS
    KOKORO_AVAILABLE = True
    log("INIT", "Kokoro TTS module loaded successfully", "SUCCESS")
except ImportError as e:
    KOKORO_AVAILABLE = False
    log("INIT", f"Kokoro TTS not available: {e}", "WARNING")

# Local STT (Faster-Whisper)
try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
    log("INIT", "Faster-Whisper module loaded successfully", "SUCCESS")
except ImportError as e:
    FASTER_WHISPER_AVAILABLE = False
    log("INIT", f"Faster-Whisper not available: {e}", "WARNING")

# Global STT model (lazy-loaded)
_stt_model = None

# Load environment variables
load_dotenv()

# Startup banner
print("\n" + "="*60, flush=True)
print("🐘 ZOOCARI - Zoo Q&A Chatbot", flush=True)
print("="*60, flush=True)
log("INIT", "Environment variables loaded", "INFO")

# Initialize OpenAI client
client = OpenAI()
log("INIT", "OpenAI client initialized", "SUCCESS")

# Initialize ElevenLabs client (optional - only if API key is set)
elevenlabs_client = None
if os.getenv("ELEVENLABS_API_KEY"):
    elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
    log("INIT", "ElevenLabs client initialized", "SUCCESS")
else:
    log("INIT", "ElevenLabs API key not found - cloud TTS fallback disabled", "WARNING")

# Database settings
DB_PATH = "data/zoo_lancedb"
TABLE_NAME = "animals"

# ============================================================
# ZUCARI THE ELEPHANT - PERSONA & PROMPTS
# ============================================================

ZUCARI_SYSTEM_PROMPT = """You are Zoocari the Elephant, the friendly animal expert at Leesburg Animal Park! You LOVE helping kids learn about all the amazing animals they can meet at the park!

🐘 YOUR PERSONALITY:
- You're warm, playful, and encouraging - like a fun zoo guide!
- You use simple words that 6-12 year olds understand
- You show genuine excitement about animal facts
- You speak like a fun friend, not a boring textbook
- You occasionally make gentle elephant sounds like "Ooh!" or trumpet sounds
- You sometimes mention that kids can see these animals at Leesburg Animal Park!

🎯 CRITICAL RULES (YOU MUST FOLLOW THESE):
1. ONLY answer questions using information from the CONTEXT provided below
2. If the context doesn't contain information to answer the question, say: "Hmm, I don't know about that yet! Maybe ask one of the zookeepers when you visit Leesburg Animal Park, or check out a book from your library! 📚"
3. NEVER make up facts or guess - kids trust you!
4. Keep answers short (1-2 short paragraphs max) - keep under 100 words
5. Use age-appropriate language - no complex scientific terms without explanation
6. Handle nature's realities gently (predators hunt, but no graphic details or inappropriate content/language)

📝 RESPONSE FORMAT:
1. Start with an enthusiastic greeting related to the question
2. Give your answer based ONLY on the context
3. End with exactly 3 follow-up questions in this format:
4. no emojis in response or follow up questions

**Want to explore more? Here are some fun questions to ask me:**
1. [First follow-up question]
2. [Second follow-up question]
3. [Third follow-up question]

The follow-up questions should:
- Be related to what you just talked about
- Be things kids would find interesting
- Be about insteresting animal facts or behaviors

CONTEXT (Use ONLY this information to answer):
{context}

Remember: You're Zoocari the Elephant at Leesburg Animal Park! Be fun, be accurate, and help kids fall in love with learning about animals! 🐘"""

# ============================================================
# HELPER FUNCTIONS
# ============================================================

import re

def set_pending_question(question: str):
    """Callback to set pending question - avoids double-click issue."""
    st.session_state.pending_question = question


def extract_followup_questions(response: str) -> tuple[str, list[str]]:
    """
    Extract follow-up questions from Zoocari's response.
    Returns (main_response, list_of_questions)
    """
    # Pattern to find the follow-up section
    pattern = r'\*\*Want to explore more\?.*?\*\*\s*\n((?:\d+\.\s+.+\n?)+)'
    match = re.search(pattern, response, re.IGNORECASE)

    if match:
        # Extract the questions part
        questions_text = match.group(1)
        # Parse individual questions
        questions = re.findall(r'\d+\.\s+(.+?)(?:\n|$)', questions_text)
        questions = [q.strip().rstrip('?') + '?' for q in questions if q.strip()]

        # Get main response (everything before the follow-up section)
        main_response = response[:match.start()].strip()
        return main_response, questions

    return response, []


# ============================================================
# VOICE FUNCTIONS (Chained Architecture: STT → LLM → TTS)
# ============================================================

def get_stt_model():
    """Get or initialize the Faster-Whisper model (lazy-loaded)."""
    global _stt_model
    if _stt_model is None:
        log("STT", "Initializing Faster-Whisper model (base, int8)...", "STT")
        start_time = time.time()
        _stt_model = WhisperModel("base", device="cpu", compute_type="int8")
        elapsed = (time.time() - start_time) * 1000
        log("STT", f"Faster-Whisper model loaded in {elapsed:.0f}ms", "SUCCESS")
    return _stt_model


def transcribe_audio_local(audio_bytes: bytes) -> str:
    """
    Local STT using Faster-Whisper - no API calls.
    ~60% faster than OpenAI API, zero cost, works offline.
    """
    import tempfile
    import os as temp_os

    # Write audio to temp file (Faster-Whisper requires file path)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(audio_bytes)
        temp_path = f.name

    try:
        model = get_stt_model()
        segments, _ = model.transcribe(temp_path, language="en")
        text = " ".join([seg.text for seg in segments]).strip()
        return text
    finally:
        temp_os.unlink(temp_path)


def transcribe_audio_openai(audio_bytes: bytes) -> str:
    """
    Cloud STT using OpenAI's Whisper API.
    Used as fallback when local STT is unavailable or fails.
    """
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = "recording.wav"

    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        language="en",
    )
    return transcription.text


def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Convert audio to text with local-first, API fallback.
    Part of the chained voice architecture: Audio → Text

    Fallback chain:
    1. Faster-Whisper (local) - ~300ms, free, offline
    2. OpenAI Whisper API (cloud) - ~800ms, paid
    """
    log("STT", f"Received audio: {len(audio_bytes)} bytes", "STT")
    start_time = time.time()

    # 1. Try local STT first (Faster-Whisper)
    if FASTER_WHISPER_AVAILABLE:
        log("STT", "Attempting Faster-Whisper (local) STT...", "STT")
        try:
            text = transcribe_audio_local(audio_bytes)
            elapsed = (time.time() - start_time) * 1000
            preview = text[:50] + "..." if len(text) > 50 else text
            log("STT", f"FASTER-WHISPER (local) succeeded in {elapsed:.0f}ms: \"{preview}\"", "SUCCESS")
            return text
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            log("STT", f"Faster-Whisper failed after {elapsed:.0f}ms: {e}", "WARNING")
    else:
        log("STT", "Faster-Whisper not available, using API fallback", "WARNING")

    # 2. Fallback to OpenAI Whisper API
    log("STT", "Attempting OpenAI Whisper (cloud) STT...", "STT")
    fallback_start = time.time()
    try:
        text = transcribe_audio_openai(audio_bytes)
        elapsed = (time.time() - fallback_start) * 1000
        total_elapsed = (time.time() - start_time) * 1000
        preview = text[:50] + "..." if len(text) > 50 else text
        log("STT", f"OPENAI (cloud) succeeded in {elapsed:.0f}ms (total: {total_elapsed:.0f}ms): \"{preview}\"", "SUCCESS")
        return text
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        log("STT", f"All STT methods failed after {elapsed:.0f}ms: {e}", "ERROR")
        raise


def generate_speech(text: str, voice: str = "nova") -> bytes:
    """
    Convert text to speech with optimized fallback chain.

    Priority (optimized for Docker/cloud deployment):
    1. OpenAI TTS (cloud) - fast, reliable, ~300-800ms
    2. ElevenLabs (cloud) - high quality, ~500-2000ms
    3. Kokoro (local) - only if TTS_PROVIDER=kokoro (slow on CPU)

    OpenAI Voice Options:
    - "nova" - Warm, engaging female (default, kid-friendly)
    - "alloy" - Neutral, balanced
    - "shimmer" - Expressive female
    """
    log("TTS", f"Starting TTS generation for {len(text)} chars, voice={voice}", "TTS")

    # Clean text for TTS (remove markdown formatting)
    clean_text = strip_markdown(text)
    log("TTS", f"Cleaned text: {len(clean_text)} chars", "INFO")

    # Check if user explicitly wants Kokoro (for native/GPU environments)
    tts_provider = os.getenv("TTS_PROVIDER", "openai").lower()

    # 1. Try Kokoro ONLY if explicitly configured (slow on CPU)
    if tts_provider == "kokoro" and KOKORO_AVAILABLE and is_kokoro_available():
        log("TTS", "Attempting Kokoro (local) TTS...", "TTS")
        start_time = time.time()
        try:
            kokoro_voice = "af_heart" if voice in ["nova", "shimmer"] else "am_adam"
            audio = generate_speech_kokoro(clean_text, voice=kokoro_voice)
            elapsed = (time.time() - start_time) * 1000
            log("TTS", f"KOKORO (local) succeeded in {elapsed:.0f}ms, {len(audio)} bytes", "SUCCESS")
            return audio
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            log("TTS", f"Kokoro failed after {elapsed:.0f}ms: {e}", "WARNING")

    # 2. OpenAI TTS - fast and reliable (~300-800ms)
    log("TTS", "Attempting OpenAI (cloud) TTS...", "TTS")
    start_time = time.time()
    try:
        with client.audio.speech.with_streaming_response.create(
            model="tts-1",
            voice=voice if voice in ["alloy", "echo", "fable", "onyx", "nova", "shimmer"] else "nova",
            input=clean_text[:4096],  # OpenAI TTS limit
        ) as response:
            audio_bytes = response.read()
            elapsed = (time.time() - start_time) * 1000
            log("TTS", f"OPENAI (cloud) succeeded in {elapsed:.0f}ms, {len(audio_bytes)} bytes", "SUCCESS")
            return audio_bytes
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        log("TTS", f"OpenAI TTS failed after {elapsed:.0f}ms: {e}", "WARNING")

    # 3. Fallback to ElevenLabs (cloud)
    if elevenlabs_client:
        log("TTS", "Attempting ElevenLabs (cloud) TTS...", "TTS")
        start_time = time.time()
        try:
            elevenlabs_voice_map = {
                "nova": "21m00Tcm4TlvDq8ikWAM",     # Rachel
                "shimmer": "EXAVITQu4vr4xnSDxMaL",  # Bella
                "alloy": "TxGEqnHWrfWFTfGW9XjX",    # Josh
            }
            voice_id = elevenlabs_voice_map.get(voice, "21m00Tcm4TlvDq8ikWAM")

            audio = elevenlabs_client.text_to_speech.convert(
                voice_id=voice_id,
                text=clean_text[:5000],
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128"
            )
            audio_bytes = b"".join(audio)
            elapsed = (time.time() - start_time) * 1000
            log("TTS", f"ELEVENLABS (cloud) succeeded in {elapsed:.0f}ms, {len(audio_bytes)} bytes", "SUCCESS")
            return audio_bytes
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            log("TTS", f"ElevenLabs failed after {elapsed:.0f}ms: {e}", "WARNING")

    raise RuntimeError("All TTS providers failed")


# ============================================================
# DATABASE FUNCTIONS
# ============================================================

@st.cache_resource
def init_db():
    """Initialize database connection."""
    log("DB", f"Connecting to LanceDB at {DB_PATH}", "DB")
    try:
        db = lancedb.connect(DB_PATH)
        table = db.open_table(TABLE_NAME)
        log("DB", f"Database connected, table '{TABLE_NAME}' loaded", "SUCCESS")
        return table
    except Exception as e:
        log("DB", f"Database connection failed: {e}", "ERROR")
        return None


def get_context(query: str, table, num_results: int = 5) -> tuple[str, list, float]:
    """Search the database for relevant context."""
    log("DB", f"Searching for: \"{query[:50]}...\"", "DB")
    start_time = time.time()

    results = table.search(query).limit(num_results).to_pandas()

    contexts = []
    sources = []
    distances = []

    for _, row in results.iterrows():
        metadata = row.get("metadata", {})
        if metadata is None:
            metadata = {}
        animal_name = metadata.get("animal_name", "Unknown") if isinstance(metadata, dict) else "Unknown"
        title = metadata.get("title", "") if isinstance(metadata, dict) else ""

        sources.append({"animal": animal_name, "title": title})

        if "_distance" in row:
            distances.append(row["_distance"])

        contexts.append(f"[About: {animal_name}]\n{row['text']}")

    avg_distance = sum(distances) / len(distances) if distances else 1.0
    confidence = max(0, 1 - avg_distance)

    elapsed = (time.time() - start_time) * 1000
    animals_found = [s["animal"] for s in sources]
    log("DB", f"Found {len(results)} results in {elapsed:.0f}ms: {animals_found}, confidence={confidence:.2f}", "SUCCESS")

    return "\n\n---\n\n".join(contexts), sources, confidence


def get_chat_response(messages, context: str) -> str:
    """Get streaming response from OpenAI API with Zoocari persona."""
    log("LLM", f"Generating response with gpt-4o-mini, context={len(context)} chars", "LLM")
    start_time = time.time()

    system_prompt = ZUCARI_SYSTEM_PROMPT.format(context=context)
    messages_with_context = [{"role": "system", "content": system_prompt}, *messages]

    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages_with_context,
        temperature=0.7,
        stream=True,
    )

    response = st.write_stream(stream)

    elapsed = (time.time() - start_time) * 1000
    log("LLM", f"Response generated in {elapsed:.0f}ms, {len(response)} chars", "SUCCESS")
    return response


# ============================================================
# PAGE CONFIG & STYLES
# ============================================================

st.set_page_config(
    page_title="Zoocari - Leesburg Animal Park",
    page_icon="🐘",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load external CSS from file
CSS_FILE = Path(__file__).parent / "static" / "zoocari.css"
st.markdown(load_css_file(CSS_FILE), unsafe_allow_html=True)

# ============================================================
# INITIALIZE STATE & SESSION MANAGEMENT
# ============================================================

# Generate or retrieve persistent session ID (stored in browser via query params)
def get_persistent_session_id() -> str:
    """
    Get or create a persistent session ID that survives page refreshes.
    Uses Streamlit's query parameters to store the session ID in the URL,
    which persists across refreshes within the same browser tab.
    """
    # Check if we have a session ID in query params
    query_params = st.query_params
    session_id = query_params.get("sid")

    if not session_id:
        # Generate new session ID
        session_id = str(uuid.uuid4())[:16]
        # Store in query params (survives page refresh)
        st.query_params["sid"] = session_id
        log("SESSION", f"Created new session: {session_id}", "SUCCESS")
    else:
        log("SESSION", f"Resumed existing session: {session_id}", "INFO")

    return session_id


# Initialize persistent session
if "persistent_session_id" not in st.session_state:
    st.session_state.persistent_session_id = get_persistent_session_id()

    # Get or create session in database
    session_info = get_or_create_session(st.session_state.persistent_session_id)
    st.session_state.session_info = session_info

    if session_info["is_new"]:
        log("SESSION", "New session created in database", "SUCCESS")
    else:
        log("SESSION", f"Session loaded - {session_info['message_count']} messages in history", "INFO")

# Load chat history from database on session resume
if "history_loaded" not in st.session_state:
    st.session_state.history_loaded = True
    session_id = st.session_state.persistent_session_id

    # Load existing chat history
    history = get_chat_history(session_id, limit=50)
    if history:
        st.session_state.messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in history
        ]
        # Set last question/response from history
        for msg in reversed(history):
            if msg["role"] == "assistant" and not st.session_state.get("last_response"):
                st.session_state.last_response = msg["content"]
            if msg["role"] == "user" and not st.session_state.get("last_question"):
                st.session_state.last_question = msg["content"]
            if st.session_state.get("last_response") and st.session_state.get("last_question"):
                break

        # Extract follow-up questions from last response
        if st.session_state.get("last_response"):
            _, followups = extract_followup_questions(st.session_state.last_response)
            st.session_state.followup_questions = followups

        log("SESSION", f"Loaded {len(history)} messages from history", "SUCCESS")

# Initialize remaining state variables
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_response" not in st.session_state:
    st.session_state.last_response = None
if "last_question" not in st.session_state:
    st.session_state.last_question = None
if "followup_questions" not in st.session_state:
    st.session_state.followup_questions = []
# Voice mode state
if "voice_mode" not in st.session_state:
    st.session_state.voice_mode = False
if "last_audio_response" not in st.session_state:
    st.session_state.last_audio_response = None

# Initialize database
table = init_db()

if table is None:
    st.error("⚠️ Database not found. Run: `python zoo_build_knowledge.py`")
    st.stop()

# ============================================================
# TWO-PANEL LAYOUT WITH COLUMNS
# ============================================================

# Create two columns for side-by-side layout with independent scroll
left_panel, right_panel = st.columns([1, 1.2])

# ============================================================
# LEFT PANEL: INPUT (Full height, scrollable)
# ============================================================
with left_panel:
    with st.container(border=False):
        # Mascot image and branding - side by side
        img_col, text_col = st.columns([1, 1])
        with img_col:
            st.image("zoocari_mascot_web.png", width=320)
        with text_col:
            st.markdown("""
            <div class="brand-header" style="text-align: left; margin: 0; display: flex; flex-direction: column; justify-content: center; height: 100%;">
                <h1 class="brand-title" style="margin: 0; font-size: 1.8rem;">Zoocari the elephant</h1>
                <p class="brand-subtitle" style="margin: 4px 0 0 0;">Your animal expert!</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div class="input-panel">
            <h2 class="input-panel-title">🔍 Ask Me About Animals!</h2>
            <p class="input-panel-subtitle">Type your question or use your voice!</p>
        </div>
        """, unsafe_allow_html=True)

        # Voice mode toggle - prominent CTA button
        voice_col1, voice_col2 = st.columns([2, 2])
        with voice_col1:
            voice_mode = st.toggle(
                "🎤 Voice Mode",
                value=st.session_state.voice_mode,
                help="Toggle voice input - speak your questions!"
            )
            st.session_state.voice_mode = voice_mode

        with voice_col2:
            if st.session_state.voice_mode:
                st.markdown("""
                <div style="background: linear-gradient(135deg, #f29021 0%, #e07800 100%);
                            border-radius: 20px; padding: 6px 12px; text-align: center;
                            border: 2px solid #f5d224;">
                    <span style="color: white; font-weight: 600; font-size: 0.8rem;">
                        🔴 Voice Active
                    </span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background: #e0ded9; border-radius: 20px; padding: 6px 12px;
                            text-align: center; opacity: 0.7;">
                    <span style="color: #3d332a; font-weight: 500; font-size: 0.8rem;">
                        📝 Text Mode
                    </span>
                </div>
                """, unsafe_allow_html=True)

        # Initialize variables
        user_question = None
        submit_button = False

        if st.session_state.voice_mode:
            # Voice input mode with enhanced UI
            st.markdown("""
            <div class="voice-mode-panel">
                <p class="voice-mode-title">🎙️ Tap the microphone to record!</p>
                <p class="voice-mode-hint">Speak clearly and I'll listen to your question</p>
            </div>
            """, unsafe_allow_html=True)

            audio_input = st.audio_input("Record your question:", key="voice_recorder", label_visibility="collapsed")

            if audio_input is not None:
                # Show recording indicator with pulse animation
                st.markdown("""
                <div class="voice-recording-active">
                    <div class="recording-indicator">
                        <span class="recording-dot"></span>
                        <p class="recording-text">🎧 Processing your voice...</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                try:
                    # st.audio_input returns UploadedFile - use getvalue() for bytes
                    audio_bytes = audio_input.getvalue()
                    user_question = transcribe_audio(audio_bytes)
                    if user_question:
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #76b9db 0%, #5a9fc4 100%);
                                    border-radius: 12px; padding: 12px 16px; margin: 8px 0;
                                    border: 2px solid #f5d224;">
                            <p style="color: white; font-weight: 600; font-size: 0.9rem; margin: 0;">
                                🗣️ You said: "{user_question}"
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                        submit_button = True
                except Exception as e:
                    st.error(f"Could not transcribe audio: {e}")
        else:
            # Text input mode (original form)
            with st.form(key="question_form", clear_on_submit=True):
                user_question = st.text_input(
                    "Your question:",
                    placeholder="What do lemurs eat? How fast can a cheetah run? 🦁🐼🦘",
                    label_visibility="collapsed"
                )
                submit_button = st.form_submit_button("🐘 Ask Zoocari!", use_container_width=True)

        # Quick question buttons
        st.markdown('<p style="color: #3d332a; margin: 6px 0 4px 0; font-size: 0.7rem; font-weight: 600;">⚡ Quick:</p>', unsafe_allow_html=True)

        q_row1 = st.columns(3)
        q_row2 = st.columns(3)

        quick_questions = [
            ("🐒", "Lemurs"), ("🐪", "Camels"), ("🦘", "Emus"),
            ("🐆", "Servals"), ("🦔", "Porcupines"), ("🦒", "Giraffes")
        ]

        for i, (emoji, animal) in enumerate(quick_questions[:3]):
            q_row1[i].button(
                f"{emoji} {animal}",
                key=f"quick_{i}",
                use_container_width=True,
                on_click=set_pending_question,
                args=(f"Tell me about {animal.lower()}!",)
            )

        for i, (emoji, animal) in enumerate(quick_questions[3:]):
            q_row2[i].button(
                f"{emoji} {animal}",
                key=f"quick_{i+3}",
                use_container_width=True,
                on_click=set_pending_question,
                args=(f"Tell me about {animal.lower()}!",)
            )

        # Session info and New Chat button
        st.markdown("---")
        session_col1, session_col2 = st.columns([2, 1])

        with session_col1:
            # Show session stats
            stats = get_session_stats(st.session_state.persistent_session_id)
            if stats["message_count"] > 0:
                st.markdown(f"""
                <div style="font-size: 0.75rem; color: #666; padding: 4px 0;">
                    📊 This session: {stats["message_count"]} messages
                </div>
                """, unsafe_allow_html=True)

        with session_col2:
            # New Chat button
            if st.button("🔄 New Chat", use_container_width=True, help="Start a fresh conversation"):
                # Generate new session ID and clear state
                new_session_id = str(uuid.uuid4())[:16]
                st.query_params["sid"] = new_session_id
                st.session_state.clear()
                st.rerun()

        # Footer in left panel
        st.markdown("""
        <div class="footer">
            <p class="footer-text">
                <a href="https://leesburganimalpark.com" target="_blank" class="footer-link">Leesburg Animal Park</a>
            </p>
        </div>
        """, unsafe_allow_html=True)

# Handle pending question from quick buttons
if "pending_question" in st.session_state:
    user_question = st.session_state.pending_question
    del st.session_state.pending_question
    submit_button = True

# ============================================================
# RIGHT PANEL: RESPONSE (Full height, scrollable)
# ============================================================
with right_panel:
    response_container = st.container(border=False)

with response_container:
    # Show chat history if there are previous messages
    history_messages = st.session_state.get("messages", [])
    if len(history_messages) > 2:  # More than just the current Q&A pair
        with st.expander(f"📜 Chat History ({len(history_messages) // 2} conversations)", expanded=False):
            # Show older messages (all except the last pair)
            for i in range(0, len(history_messages) - 2, 2):
                if i + 1 < len(history_messages) - 2:
                    user_msg = history_messages[i]
                    assistant_msg = history_messages[i + 1]

                    if user_msg["role"] == "user":
                        st.markdown(f"""
                        <div style="background: #f0f2f6; border-radius: 8px; padding: 8px 12px; margin: 4px 0;">
                            <span style="font-weight: 600; color: #3d332a;">🧒 You:</span>
                            <span style="color: #555;">{sanitize_html(user_msg["content"][:100])}{'...' if len(user_msg["content"]) > 100 else ''}</span>
                        </div>
                        """, unsafe_allow_html=True)

                    if assistant_msg["role"] == "assistant":
                        # Extract main response without follow-ups
                        main_resp, _ = extract_followup_questions(assistant_msg["content"])
                        st.markdown(f"""
                        <div style="background: #e8f4ea; border-radius: 8px; padding: 8px 12px; margin: 4px 0 12px 0;">
                            <span style="font-weight: 600; color: #2d5a3d;">🐘 Zoocari:</span>
                            <span style="color: #555;">{sanitize_html(main_resp[:150])}{'...' if len(main_resp) > 150 else ''}</span>
                        </div>
                        """, unsafe_allow_html=True)

    if submit_button and user_question:
        # Add new question to messages (don't clear history)
        st.session_state.messages.append({"role": "user", "content": user_question})
        st.session_state.last_question = user_question

        # Save user message to database
        save_message(
            st.session_state.persistent_session_id,
            "user",
            user_question
        )
        log("SESSION", f"Saved user message to database", "DB")

        # Response container
        st.markdown('<div class="response-container">', unsafe_allow_html=True)

        # Question display (sanitize user input to prevent XSS)
        safe_question = sanitize_html(user_question)
        st.markdown(f"""
        <div class="question-display">
            <p class="question-label">You Asked:</p>
            <p class="question-text">{safe_question}</p>
        </div>
        """, unsafe_allow_html=True)

        # Response header
        st.markdown("""
        <div class="response-header">
            <span style="font-size: 1.5rem;">🐘</span>
            <p class="response-header-text">Zoocari Says:</p>
        </div>
        """, unsafe_allow_html=True)

        # Get context
        context, sources, confidence = get_context(user_question, table)

        # Response body - use placeholder so we can replace after streaming
        st.markdown('<div class="response-body">', unsafe_allow_html=True)
        response_placeholder = st.empty()
        with response_placeholder.container():
            response = get_chat_response(st.session_state.messages, context)

        # Extract follow-ups and replace with clean response
        main_response, followups = extract_followup_questions(response)
        st.session_state.followup_questions = followups

        # Replace streamed content with main response only (no follow-ups)
        response_placeholder.markdown(main_response)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # Save full response to session state
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.session_state.last_response = response

        # Save assistant message to database with metadata
        save_message(
            st.session_state.persistent_session_id,
            "assistant",
            response,
            metadata={"confidence": confidence, "sources": [s["animal"] for s in sources]}
        )
        log("SESSION", f"Saved assistant response to database", "DB")

        # Generate and play TTS audio response with styled player
        with st.spinner("🔊 Generating voice response..."):
            try:
                audio_bytes = generate_speech(main_response)
                st.session_state.last_audio_response = audio_bytes

                # Styled audio player header
                st.markdown("""
                <div class="audio-player-wrapper">
                    <div class="audio-player-header">
                        <span class="audio-player-icon">🔊</span>
                        <p class="audio-player-label">Listen to Zoocari's Response</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.audio(audio_bytes, format="audio/mp3", autoplay=True)
            except Exception:
                st.warning("Could not generate audio response.")

        # Display follow-up buttons
        if followups:
            st.markdown("""
            <div class="followup-section">
                <p class="followup-title">🔮 Want to explore more? Click a question:</p>
            </div>
            """, unsafe_allow_html=True)
            for i, question in enumerate(followups):
                st.button(
                    f"❓ {question}",
                    key=f"followup_{i}",
                    use_container_width=True,
                    on_click=set_pending_question,
                    args=(question,)
                )

    # Show previous response on page refresh
    elif st.session_state.last_question and st.session_state.last_response:
        st.markdown('<div class="response-container">', unsafe_allow_html=True)

        # Sanitize stored question for safe rendering
        safe_last_question = sanitize_html(st.session_state.last_question)
        st.markdown(f"""
        <div class="question-display">
            <p class="question-label">You Asked:</p>
            <p class="question-text">{safe_last_question}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="response-header">
            <span style="font-size: 1.5rem;">🐘</span>
            <p class="response-header-text">Zoocari Says:</p>
        </div>
        """, unsafe_allow_html=True)

        # Extract main response without follow-ups for cleaner display
        main_response, _ = extract_followup_questions(st.session_state.last_response)
        st.markdown('<div class="response-body">', unsafe_allow_html=True)
        st.markdown(main_response)
        st.markdown('</div></div>', unsafe_allow_html=True)

        # Show styled audio player for previous response if available
        if st.session_state.last_audio_response:
            st.markdown("""
            <div class="audio-player-wrapper">
                <div class="audio-player-header">
                    <span class="audio-player-icon">🔊</span>
                    <p class="audio-player-label">Listen to Zoocari's Response</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.audio(st.session_state.last_audio_response, format="audio/mp3")

        # Display follow-up buttons from session state
        followups = st.session_state.get("followup_questions", [])
        if followups:
            st.markdown("""
            <div class="followup-section">
                <p class="followup-title">🔮 Want to explore more? Click a question:</p>
            </div>
            """, unsafe_allow_html=True)
            for i, question in enumerate(followups):
                st.button(
                    f"❓ {question}",
                    key=f"followup_prev_{i}",
                    use_container_width=True,
                    on_click=set_pending_question,
                    args=(question,)
                )

    # Welcome message when no question asked yet
    else:
        st.markdown("""
        <div class="welcome-box">
            <h2 class="welcome-title">👋 Welcome, Young Explorer!</h2>
            <p class="welcome-text">
                I'm Zoocari the Elephant, and I LOVE helping kids learn about animals!<br>
                Ask me about any animals you see at Leesburg Animal Park —
                like lemurs, camels, emus, servals, and so many more!
            </p>
            <p class="welcome-hint">
                💡 Type a question on the left or click a quick question button to get started!
            </p>
        </div>
        """, unsafe_allow_html=True)
