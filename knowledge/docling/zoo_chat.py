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
from openai import OpenAI
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv

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
4. Keep answers short (1-2 short paragraphs max)
5. Use age-appropriate language - no complex scientific terms without explanation
6. Handle nature's realities gently (predators hunt, but no graphic details)
7. Include 2 or 3 fun facts/statistics to make learning fun

📝 RESPONSE FORMAT:
1. Start with an enthusiastic greeting related to the question
2. Give your answer based ONLY on the context
3. End with exactly 3 follow-up questions in this format:

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

def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Convert audio to text using OpenAI's Whisper API.
    Part of the chained voice architecture: Audio → Text
    """
    log("STT", f"Received audio: {len(audio_bytes)} bytes", "STT")
    start_time = time.time()

    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = "recording.wav"

    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        language="en",
    )

    elapsed = (time.time() - start_time) * 1000
    log("STT", f"Transcription complete in {elapsed:.0f}ms: \"{transcription.text[:50]}...\"", "SUCCESS")
    return transcription.text


def generate_speech(text: str, voice: str = "af_bella") -> bytes:
    """
    Convert text to speech with tiered fallback for optimal latency:
    1. Kokoro (local) - fastest, free, ~50-200ms
    2. ElevenLabs (cloud) - high quality, ~500-2000ms
    3. OpenAI (cloud) - reliable fallback, ~300-800ms

    Kokoro Voice Options (kid-friendly):
    - "af_bella" - Friendly female, clear pronunciation (default)
    - "af_nova" - Warm, engaging female
    - "af_heart" - Expressive, upbeat female
    - "am_adam" - Clear male voice

    Falls back to cloud TTS if local inference fails.
    """
    log("TTS", f"Starting TTS generation for {len(text)} chars, voice={voice}", "TTS")

    # Clean text for TTS (remove markdown formatting)
    clean_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Remove bold
    clean_text = re.sub(r'\*([^*]+)\*', r'\1', clean_text)  # Remove italic
    clean_text = re.sub(r'#{1,6}\s*', '', clean_text)  # Remove headers
    log("TTS", f"Cleaned text: {len(clean_text)} chars", "INFO")

    # 1. Try Kokoro (local) first - fastest option
    if KOKORO_AVAILABLE and is_kokoro_available():
        log("TTS", "Attempting Kokoro (local) TTS...", "TTS")
        start_time = time.time()
        try:
            audio = generate_speech_kokoro(clean_text, voice=voice)
            elapsed = (time.time() - start_time) * 1000
            log("TTS", f"✅ KOKORO (local) succeeded in {elapsed:.0f}ms, {len(audio)} bytes", "SUCCESS")
            return audio
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            log("TTS", f"Kokoro failed after {elapsed:.0f}ms: {e}", "WARNING")
    else:
        log("TTS", "Kokoro not available, skipping local TTS", "WARNING")

    # 2. Fallback to ElevenLabs (cloud)
    if elevenlabs_client:
        log("TTS", "Attempting ElevenLabs (cloud) TTS...", "TTS")
        start_time = time.time()
        try:
            # Map Kokoro voice to ElevenLabs voice ID
            elevenlabs_voice_map = {
                "af_bella": "EXAVITQu4vr4xnSDxMaL",  # Bella
                "af_nova": "21m00Tcm4TlvDq8ikWAM",   # Rachel
                "am_adam": "TxGEqnHWrfWFTfGW9XjX",   # Josh
            }
            voice_id = elevenlabs_voice_map.get(voice, "iEbJsqzb6jw8MYxZ2xca")
            log("TTS", f"Using ElevenLabs voice_id={voice_id}", "INFO")

            audio = elevenlabs_client.text_to_speech.convert(
                voice_id=voice_id,
                text=clean_text[:5000],  # ElevenLabs limit
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128"
            )
            audio_bytes = b"".join(audio)
            elapsed = (time.time() - start_time) * 1000
            log("TTS", f"✅ ELEVENLABS (cloud) succeeded in {elapsed:.0f}ms, {len(audio_bytes)} bytes", "SUCCESS")
            return audio_bytes
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            log("TTS", f"ElevenLabs failed after {elapsed:.0f}ms: {e}", "WARNING")
    else:
        log("TTS", "ElevenLabs client not configured, skipping", "WARNING")

    # 3. Final fallback to OpenAI TTS
    log("TTS", "Attempting OpenAI (cloud) TTS as final fallback...", "TTS")
    start_time = time.time()
    with client.audio.speech.with_streaming_response.create(
        model="tts-1",
        voice="nova",
        input=clean_text[:4096],  # OpenAI TTS limit
    ) as response:
        audio_bytes = response.read()
        elapsed = (time.time() - start_time) * 1000
        log("TTS", f"✅ OPENAI (cloud) succeeded in {elapsed:.0f}ms, {len(audio_bytes)} bytes", "SUCCESS")
        return audio_bytes


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

# Complete CSS with dual-panel independent scrolling layout
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&family=Rubik:wght@400;500;700;900&display=swap');

    /* ============================================
       LEESBURG ANIMAL PARK COLOR SYSTEM
       ============================================ */
    :root {
        --leesburg-yellow: #f5d224;
        --leesburg-brown: #3d332a;
        --leesburg-beige: #f4f2ef;
        --leesburg-orange: #f29021;
        --leesburg-blue: #76b9db;
        --leesburg-white: #ffffff;
    }

    /* ============================================
       GLOBAL STYLES - FULL VIEWPORT LAYOUT
       ============================================ */
    .stApp {
        background-color: var(--leesburg-beige);
    }

    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Main content - remove scroll, we handle it ourselves */
    .main .block-container {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        max-width: 100% !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
    }

    /* ============================================
       BASE LAYOUT (mobile-first)
       ============================================ */
    [data-testid="stAppViewBlockContainer"] {
        padding: 0 !important;
    }

    .main .block-container {
        padding: 10px 20px !important;
        max-width: 100% !important;
    }

    [data-testid="stHorizontalBlock"] {
        align-items: stretch !important;
    }

    /* Panel styling */
    [data-testid="stVerticalBlockBorderWrapper"] > div,
    [data-testid="stVerticalBlockBorderWrapper"] > div[style*="height"] {
        border-radius: 16px !important;
        background-color: var(--leesburg-white) !important;
        box-shadow: 0 4px 24px rgba(61, 51, 42, 0.12) !important;
        border: 2px solid var(--leesburg-yellow) !important;
    }

    /* Left panel specific styling */
    .stColumn:first-child [data-testid="stVerticalBlockBorderWrapper"] > div {
        background: linear-gradient(180deg, var(--leesburg-beige) 0%, var(--leesburg-white) 100%) !important;
    }

    /* Right panel specific styling */
    .stColumn:last-child [data-testid="stVerticalBlockBorderWrapper"] > div {
        background-color: var(--leesburg-white) !important;
    }

    /* ============================================
       TYPOGRAPHY
       ============================================ */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Rubik', sans-serif !important;
        color: var(--leesburg-brown) !important;
    }

    p, span, li, div {
        font-family: 'Poppins', sans-serif;
        color: var(--leesburg-brown);
    }

    /* ============================================
       INPUT PANEL - Compact
       ============================================ */
    .input-panel {
        background: linear-gradient(135deg, var(--leesburg-brown) 0%, #4a3f35 100%);
        border-radius: 10px;
        padding: 10px 14px;
        margin-bottom: 8px;
        box-shadow: 0 4px 16px rgba(61, 51, 42, 0.2);
        border: 2px solid var(--leesburg-yellow);
    }

    .input-panel-title {
        font-family: 'Rubik', sans-serif;
        font-weight: 900;
        font-size: 1rem;
        color: var(--leesburg-yellow);
        margin: 0 0 2px 0;
        text-align: center;
    }

    .input-panel-subtitle {
        font-family: 'Poppins', sans-serif;
        font-size: 0.75rem;
        color: var(--leesburg-white);
        text-align: center;
        margin-bottom: 0;
        opacity: 0.9;
    }

    /* ============================================
       QUICK QUESTION BUTTONS - Compact
       ============================================ */
    .stButton > button {
        background-color: var(--leesburg-yellow) !important;
        color: var(--leesburg-brown) !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 4px 10px !important;
        font-family: 'Poppins', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.7rem !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 6px rgba(245, 210, 36, 0.2) !important;
    }

    .stButton > button:hover {
        background-color: var(--leesburg-orange) !important;
        color: var(--leesburg-white) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 3px 10px rgba(242, 144, 33, 0.3) !important;
    }

    /* Form submit button */
    .stFormSubmitButton > button {
        background-color: var(--leesburg-yellow) !important;
        color: var(--leesburg-brown) !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 6px 16px !important;
        font-family: 'Rubik', sans-serif !important;
        font-weight: 700 !important;
        font-size: 0.85rem !important;
    }

    .stFormSubmitButton > button:hover {
        background-color: var(--leesburg-orange) !important;
        color: var(--leesburg-white) !important;
    }

    /* ============================================
       TEXT INPUT STYLING - Compact
       ============================================ */
    .stTextInput > div > div > input {
        background-color: var(--leesburg-white) !important;
        border: 2px solid var(--leesburg-yellow) !important;
        border-radius: 8px !important;
        padding: 8px 12px !important;
        font-family: 'Poppins', sans-serif !important;
        font-size: 0.9rem !important;
        color: var(--leesburg-brown) !important;
    }

    .stTextInput > div > div > input:focus {
        border-color: var(--leesburg-orange) !important;
        box-shadow: 0 0 0 2px rgba(245, 210, 36, 0.3) !important;
    }

    .stTextInput > div > div > input::placeholder {
        color: #999 !important;
        opacity: 0.7 !important;
        font-size: 0.8rem !important;
    }

    /* ============================================
       RESPONSE AREA - Compact
       ============================================ */
    .response-container {
        background-color: var(--leesburg-white);
        border-radius: 10px;
        padding: 0;
        margin-top: 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
        overflow: hidden;
    }

    .question-display {
        background: linear-gradient(135deg, var(--leesburg-yellow) 0%, #e8c41f 100%);
        padding: 8px 14px;
        border-bottom: 2px solid var(--leesburg-brown);
    }

    .question-label {
        font-family: 'Rubik', sans-serif;
        font-weight: 700;
        font-size: 0.7rem;
        color: var(--leesburg-brown);
        margin-bottom: 2px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .question-text {
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        font-size: 0.95rem;
        color: var(--leesburg-brown);
        margin: 0;
    }

    .response-header {
        background-color: var(--leesburg-brown);
        padding: 6px 14px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .response-header-text {
        font-family: 'Rubik', sans-serif;
        font-weight: 700;
        font-size: 0.9rem;
        color: var(--leesburg-yellow);
        margin: 0;
    }

    .response-body {
        padding: 10px 14px;
        background-color: #fafaf8;
        min-height: 30px;
    }

    .response-body p {
        font-family: 'Poppins', sans-serif;
        font-size: 0.9rem;
        line-height: 1.5;
        color: var(--leesburg-brown);
    }

    .response-body strong {
        color: var(--leesburg-brown);
        font-weight: 700;
    }

    .response-body li {
        margin-bottom: 4px;
        font-size: 0.9rem;
    }

    /* ============================================
       WELCOME BOX - Compact
       ============================================ */
    .welcome-box {
        background: linear-gradient(135deg, var(--leesburg-brown) 0%, #4a3f35 100%);
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 16px rgba(61, 51, 42, 0.2);
        border-left: 4px solid var(--leesburg-yellow);
    }

    .welcome-title {
        font-family: 'Rubik', sans-serif;
        font-weight: 900;
        font-size: 1.1rem;
        color: var(--leesburg-yellow);
        margin-bottom: 8px;
    }

    .welcome-text {
        font-family: 'Poppins', sans-serif;
        font-size: 0.85rem;
        color: var(--leesburg-white);
        line-height: 1.4;
        margin-bottom: 8px;
    }

    .welcome-hint {
        font-family: 'Poppins', sans-serif;
        font-size: 0.75rem;
        color: var(--leesburg-blue);
        font-style: italic;
    }

    /* ============================================
       QUICK QUESTIONS ROW - Compact
       ============================================ */
    .quick-questions-label {
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        font-size: 0.7rem;
        color: var(--leesburg-brown);
        margin: 4px 0;
    }

    /* ============================================
       HEADER BRANDING - Compact
       ============================================ */
    .brand-header {
        text-align: center;
        margin-bottom: 8px;
    }

    .brand-logo {
        font-size: 1.5rem;
        margin-bottom: 0;
        display: inline;
    }

    .brand-title {
        font-family: 'Rubik', sans-serif;
        font-weight: 900;
        font-size: 1.2rem;
        color: var(--leesburg-brown);
        margin: 0;
        display: inline;
    }

    .brand-subtitle {
        font-family: 'Poppins', sans-serif;
        font-weight: 500;
        font-size: 0.75rem;
        color: var(--leesburg-brown);
        opacity: 0.8;
        margin: 0;
    }

    /* ============================================
       STATUS INDICATOR - Hide
       ============================================ */
    [data-testid="stStatus"] {
        display: none !important;
    }

    /* ============================================
       AGGRESSIVE WHITESPACE REMOVAL - RIGHT PANEL
       ============================================ */
    .stColumn:last-child [data-testid="stVerticalBlockBorderWrapper"] > div > div,
    .stColumn:last-child [data-testid="stVerticalBlockBorderWrapper"] > div > div > div {
        gap: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    .stColumn:last-child .stMarkdown {
        margin: 0 !important;
        padding: 0 !important;
    }

    .stColumn:last-child .stMarkdown p {
        margin: 0 0 0.75rem 0 !important;
    }

    .stColumn:last-child .element-container {
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Remove empty placeholder spacing */
    .stColumn:last-child [data-testid="stEmpty"] {
        display: none !important;
    }

    /* Compact the response container */
    .response-container {
        margin: 0 !important;
    }

    .question-display {
        margin-bottom: 0 !important;
    }

    .response-header {
        margin: 0 !important;
    }

    /* ============================================
       FOOTER - Compact
       ============================================ */
    .footer {
        background-color: var(--leesburg-brown);
        border-radius: 8px;
        padding: 8px 12px;
        text-align: center;
        margin-top: 10px;
    }

    .footer-text {
        font-family: 'Poppins', sans-serif;
        font-size: 0.65rem;
        color: var(--leesburg-white);
        opacity: 0.8;
        margin: 0;
        line-height: 1.3;
    }

    .footer-link {
        color: var(--leesburg-yellow);
        text-decoration: none;
        font-weight: 600;
    }

    .footer-link:hover {
        color: var(--leesburg-orange);
    }

    /* ============================================
       FOLLOW-UP QUESTION BUTTONS - Compact
       ============================================ */
    .followup-section {
        background: linear-gradient(135deg, var(--leesburg-brown) 0%, #4a3f35 100%);
        border-radius: 8px;
        padding: 8px 12px;
        margin-top: 8px;
    }

    .followup-title {
        font-family: 'Rubik', sans-serif;
        font-weight: 700;
        font-size: 0.75rem;
        color: var(--leesburg-yellow);
        margin-bottom: 6px;
    }

    /* Style follow-up buttons in right panel */
    .stColumn:last-child .stButton > button {
        background-color: var(--leesburg-yellow) !important;
        color: var(--leesburg-brown) !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 6px 12px !important;
        font-family: 'Poppins', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.75rem !important;
        text-align: left !important;
        white-space: normal !important;
        height: auto !important;
        min-height: 28px !important;
        line-height: 1.3 !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 6px rgba(245, 210, 36, 0.2) !important;
    }

    .stColumn:last-child .stButton > button:hover {
        background-color: var(--leesburg-orange) !important;
        color: var(--leesburg-white) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(242, 144, 33, 0.4) !important;
    }

    /* ============================================
       DESKTOP FIXED HEIGHT PANELS
       ============================================ */
    @media screen and (min-width: 769px) {
        .stApp, .main, [data-testid="stAppViewContainer"] {
            height: 100vh !important;
            overflow: hidden !important;
        }

        [data-testid="stAppViewBlockContainer"] {
            height: 100vh !important;
        }

        [data-testid="stHorizontalBlock"] {
            height: calc(100vh - 20px) !important;
        }

        .stColumn {
            height: 100% !important;
        }

        [data-testid="stVerticalBlockBorderWrapper"],
        [data-testid="stVerticalBlockBorderWrapper"] > div {
            height: calc(100vh - 40px) !important;
            max-height: calc(100vh - 40px) !important;
            overflow-y: auto !important;
        }
    }

    /* ============================================
       MOBILE RESPONSIVE STYLES
       ============================================ */
    @media screen and (max-width: 768px) {
        /* Improve touch scrolling */
        * {
            -webkit-tap-highlight-color: transparent;
        }

        /* Allow page to scroll naturally on mobile */
        .stApp, .main, [data-testid="stAppViewContainer"] {
            height: auto !important;
            min-height: 100vh !important;
            overflow: auto !important;
            -webkit-overflow-scrolling: touch !important;
        }

        [data-testid="stAppViewBlockContainer"] {
            height: auto !important;
            padding: 10px !important;
        }

        .main .block-container {
            padding: 8px !important;
            height: auto !important;
        }

        /* Stack columns vertically */
        [data-testid="stHorizontalBlock"] {
            flex-direction: column !important;
            height: auto !important;
            gap: 16px !important;
        }

        .stColumn {
            width: 100% !important;
            height: auto !important;
        }

        /* Fix container heights for mobile */
        [data-testid="stVerticalBlockBorderWrapper"],
        [data-testid="stVerticalBlockBorderWrapper"] > div,
        [data-testid="stVerticalBlockBorderWrapper"] > div[style*="height"] {
            height: auto !important;
            max-height: none !important;
            min-height: auto !important;
        }

        /* Mobile mascot section - stack vertically and center */
        .stColumn:first-child [data-testid="stHorizontalBlock"] {
            flex-direction: column !important;
            align-items: center !important;
        }

        /* Smaller mascot image on mobile */
        .stColumn:first-child [data-testid="stImage"] {
            max-width: 180px !important;
            margin: 0 auto !important;
        }

        .stColumn:first-child [data-testid="stImage"] img {
            max-width: 180px !important;
        }

        /* Center brand header on mobile */
        .brand-header {
            text-align: center !important;
            padding: 10px 0 !important;
        }

        .brand-title {
            font-size: 1.4rem !important;
        }

        .brand-subtitle {
            font-size: 0.8rem !important;
        }

        /* Input panel adjustments */
        .input-panel {
            padding: 12px !important;
            margin-bottom: 12px !important;
        }

        .input-panel-title {
            font-size: 1.1rem !important;
        }

        /* Larger touch targets for buttons */
        .stButton > button {
            padding: 10px 16px !important;
            font-size: 0.85rem !important;
            min-height: 44px !important;
            border-radius: 12px !important;
        }

        .stFormSubmitButton > button {
            padding: 12px 20px !important;
            font-size: 1rem !important;
            min-height: 48px !important;
        }

        /* Text input - larger for touch */
        .stTextInput > div > div > input {
            padding: 12px 14px !important;
            font-size: 16px !important; /* Prevents iOS zoom */
            min-height: 48px !important;
        }

        /* Quick questions - 2 columns on mobile */
        .stColumn:first-child [data-testid="stHorizontalBlock"]:not(:first-child) {
            flex-direction: row !important;
            flex-wrap: wrap !important;
        }

        /* Response container */
        .response-container {
            margin: 0 !important;
            border-radius: 12px !important;
        }

        .question-display {
            padding: 12px !important;
        }

        .question-text {
            font-size: 1rem !important;
        }

        .response-header {
            padding: 10px 12px !important;
        }

        .response-body {
            padding: 14px !important;
        }

        .response-body p {
            font-size: 0.95rem !important;
            line-height: 1.6 !important;
        }

        /* Welcome box */
        .welcome-box {
            padding: 20px 16px !important;
        }

        .welcome-title {
            font-size: 1.2rem !important;
        }

        .welcome-text {
            font-size: 0.9rem !important;
        }

        /* Follow-up buttons - larger touch targets */
        .stColumn:last-child .stButton > button {
            padding: 12px 16px !important;
            font-size: 0.9rem !important;
            min-height: 48px !important;
        }

        .followup-section {
            padding: 12px !important;
            margin-top: 12px !important;
        }

        .followup-title {
            font-size: 0.85rem !important;
        }

        /* Footer */
        .footer {
            margin-top: 16px !important;
            padding: 12px !important;
        }

        .footer-text {
            font-size: 0.75rem !important;
        }
    }

    /* Extra small screens (phones in portrait) */
    @media screen and (max-width: 480px) {
        .main .block-container {
            padding: 6px !important;
        }

        .brand-title {
            font-size: 1.2rem !important;
        }

        .stColumn:first-child [data-testid="stImage"] img {
            max-width: 140px !important;
        }

        .input-panel-title {
            font-size: 1rem !important;
        }

        /* Single column for quick questions on very small screens */
        .stColumn:first-child [data-testid="stHorizontalBlock"]:not(:first-child) .stColumn {
            flex: 0 0 50% !important;
            max-width: 50% !important;
        }
    }

    /* ============================================
       VOICE MODE - PULSE ANIMATION & STYLING
       ============================================ */

    /* Pulse animation keyframes */
    @keyframes pulse-recording {
        0% {
            box-shadow: 0 0 0 0 rgba(242, 144, 33, 0.7);
        }
        70% {
            box-shadow: 0 0 0 15px rgba(242, 144, 33, 0);
        }
        100% {
            box-shadow: 0 0 0 0 rgba(242, 144, 33, 0);
        }
    }

    @keyframes pulse-glow {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.6;
        }
    }

    /* Voice recording container with pulse effect */
    .voice-recording-active {
        background: linear-gradient(135deg, var(--leesburg-orange) 0%, #e07800 100%);
        border-radius: 16px;
        padding: 16px;
        margin: 8px 0;
        animation: pulse-recording 1.5s infinite;
        border: 3px solid var(--leesburg-yellow);
    }

    .voice-recording-active .recording-indicator {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
    }

    .recording-dot {
        width: 12px;
        height: 12px;
        background-color: #ff4444;
        border-radius: 50%;
        animation: pulse-glow 1s infinite;
    }

    .recording-text {
        font-family: 'Rubik', sans-serif;
        font-weight: 700;
        font-size: 0.9rem;
        color: var(--leesburg-white);
        margin: 0;
    }

    /* Voice mode toggle button - CTA style */
    .voice-cta-button {
        background: linear-gradient(135deg, var(--leesburg-orange) 0%, #e07800 100%) !important;
        color: var(--leesburg-white) !important;
        border: 3px solid var(--leesburg-yellow) !important;
        border-radius: 50px !important;
        padding: 12px 24px !important;
        font-family: 'Rubik', sans-serif !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(242, 144, 33, 0.4) !important;
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
    }

    .voice-cta-button:hover {
        transform: translateY(-2px) scale(1.02) !important;
        box-shadow: 0 6px 20px rgba(242, 144, 33, 0.5) !important;
    }

    .voice-cta-active {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a5a 100%) !important;
        animation: pulse-recording 1.5s infinite !important;
    }

    /* Voice mode panel styling */
    .voice-mode-panel {
        background: linear-gradient(135deg, var(--leesburg-brown) 0%, #4a3f35 100%);
        border-radius: 16px;
        padding: 16px;
        margin: 8px 0;
        border: 2px solid var(--leesburg-orange);
        text-align: center;
    }

    .voice-mode-title {
        font-family: 'Rubik', sans-serif;
        font-weight: 700;
        font-size: 1rem;
        color: var(--leesburg-orange);
        margin: 0 0 8px 0;
    }

    .voice-mode-hint {
        font-family: 'Poppins', sans-serif;
        font-size: 0.8rem;
        color: var(--leesburg-white);
        opacity: 0.9;
        margin: 0;
    }

    /* ============================================
       AUDIO PLAYER - LEESBURG BRANDING
       ============================================ */

    /* Style the Streamlit audio player container */
    .stAudio {
        margin: 12px 0 !important;
    }

    .stAudio > div {
        background: linear-gradient(135deg, var(--leesburg-brown) 0%, #4a3f35 100%) !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        border: 2px solid var(--leesburg-yellow) !important;
        box-shadow: 0 4px 12px rgba(61, 51, 42, 0.15) !important;
    }

    /* Audio element styling */
    .stAudio audio {
        width: 100% !important;
        height: 40px !important;
        border-radius: 8px !important;
    }

    /* Custom audio player wrapper */
    .audio-player-wrapper {
        background: linear-gradient(135deg, var(--leesburg-brown) 0%, #4a3f35 100%);
        border-radius: 12px;
        padding: 12px 16px;
        border: 2px solid var(--leesburg-yellow);
        margin: 12px 0;
        box-shadow: 0 4px 12px rgba(61, 51, 42, 0.15);
    }

    .audio-player-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
    }

    .audio-player-icon {
        font-size: 1.2rem;
    }

    .audio-player-label {
        font-family: 'Rubik', sans-serif;
        font-weight: 600;
        font-size: 0.8rem;
        color: var(--leesburg-yellow);
        margin: 0;
    }

    /* Style audio input widget */
    [data-testid="stAudioInput"] {
        margin: 8px 0 !important;
    }

    [data-testid="stAudioInput"] > div {
        background: linear-gradient(135deg, var(--leesburg-orange) 0%, #e07800 100%) !important;
        border-radius: 12px !important;
        padding: 8px 12px !important;
        border: 2px solid var(--leesburg-yellow) !important;
    }

    [data-testid="stAudioInput"] button {
        background-color: var(--leesburg-yellow) !important;
        color: var(--leesburg-brown) !important;
        border-radius: 50% !important;
        border: none !important;
    }

</style>
""", unsafe_allow_html=True)

# ============================================================
# INITIALIZE STATE
# ============================================================

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
    if submit_button and user_question:
        # Clear previous and add new question
        st.session_state.messages = [{"role": "user", "content": user_question}]
        st.session_state.last_question = user_question

        # Response container
        st.markdown('<div class="response-container">', unsafe_allow_html=True)

        # Question display
        st.markdown(f"""
        <div class="question-display">
            <p class="question-label">🧒 You Asked:</p>
            <p class="question-text">{user_question}</p>
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

        # Save full response
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.session_state.last_response = response

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

        st.markdown(f"""
        <div class="question-display">
            <p class="question-label">🧒 You Asked:</p>
            <p class="question-text">{st.session_state.last_question}</p>
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
