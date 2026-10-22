import time
from io import BytesIO
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
from google import genai
from google.genai import types

# PDF Reading & Generation
from pypdf import PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# PowerPoint (.pptx) Generation
from pptx import Presentation
from pptx.util import Inches, Pt

# Math Graphing
import matplotlib.pyplot as plt
import numpy as np

# Configure Muk AI Page
st.set_page_config(
    page_title="Muk AI - Ultimate AI Assistant",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- WORLD-CLASS HOLOGRAPHIC CYBERPUNK & AURORA DESIGN SYSTEM ---
futuristic_style = """
<style>
/* Import Sci-Fi Fonts */
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;800&family=Share+Tech+Mono&display=swap');

/* Hide default footers, status widgets, and viewer badges */
footer { visibility: hidden !important; }
[data-testid="stStatusWidget"] { display: none !important; }
.stDeployButton { display: none !important; }
div[class*="viewerBadge"] { display: none !important; }

/* Hide ONLY top-right toolbar action buttons while leaving left >> toggle intact */
[data-testid="stToolbar"] button,
[data-testid="stToolbar"] a,
[data-testid="stHeader"] a[href*="github"] {
    display: none !important;
    visibility: hidden !important;
}

/* Header transparency */
[data-testid="stHeader"] {
    background-color: transparent !important;
}

/* FORCE the top-left sidebar toggle button (>>) to be fully visible and glowing */
[data-testid="collapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    color: #38bdf8 !important;
    z-index: 999999 !important;
}

/* 1. Deep Space Aurora Borealis Background & CRT Scanlines */
.stApp {
    background-color: #050711;
    background-image: 
        radial-gradient(circle at 15% 20%, rgba(56, 189, 248, 0.08) 0%, transparent 40%),
        radial-gradient(circle at 85% 80%, rgba(99, 102, 241, 0.08) 0%, transparent 40%),
        linear-gradient(rgba(56, 189, 248, 0.02) 1px, transparent 1px),
        linear-gradient(90deg, rgba(56, 189, 248, 0.02) 1px, transparent 1px),
        linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.3) 50%);
    background-size: 100% 100%, 100% 100%, 35px 35px, 35px 35px, 100% 4px;
    color: #e2e8f0;
    font-family: 'Share Tech Mono', monospace;
}

/* 2. Shimmering Neon Gradient Titles */
h1, h2, h3 {
    font-family: 'Orbitron', sans-serif !important;
    background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: 1.5px;
    text-shadow: 0 0 20px rgba(56, 189, 248, 0.3);
}

/* Custom Neon Glowing Scrollbars */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: #050711;
}
::-webkit-scrollbar-thumb {
    background: #38bdf8;
    border-radius: 3px;
    box-shadow: 0 0 12px #38bdf8;
}
::-webkit-scrollbar-thumb:hover {
    background: #c084fc;
    box-shadow: 0 0 18px #c084fc;
}

/* Glassmorphism Sidebar with Aurora Glow */
section[data-testid="stSidebar"] {
    background-color: rgba(9, 13, 26, 0.92);
    backdrop-filter: blur(16px);
    border-right: 1px solid rgba(56, 189, 248, 0.25);
    box-shadow: 5px 0 25px rgba(0, 0, 0, 0.5);
}

section[data-testid="stSidebar"] p, 
section[data-testid="stSidebar"] span, 
section[data-testid="stSidebar"] label, 
section[data-testid="stSidebar"] h1, 
section[data-testid="stSidebar"] h2, 
section[data-testid="stSidebar"] h3 {
    color: #f8fafc !important;
}

/* 3. Orbiting Laser Border Beam on Inputs & TextAreas */
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
    background-color: rgba(13, 19, 38, 0.8) !important;
    border: 1px solid rgba(56, 189, 248, 0.4) !important;
    border-left: 3px solid #38bdf8 !important;
    color: #f8fafc !important;
    transition: all 0.3s ease-in-out !important;
    border-radius: 6px !important;
    backdrop-filter: blur(8px);
}
.stTextInput input:hover, .stTextArea textarea:hover, .stSelectbox div[data-baseweb="select"]:hover {
    border-color: #c084fc !important;
    box-shadow: 0 0 20px rgba(192, 132, 252, 0.4) !important;
    transform: translateY(-2px);
}

/* Cyberpunk Modular Tabs Styling */
div[data-baseweb="tab-list"] {
    gap: 8px;
    background: rgba(9, 13, 26, 0.75);
    padding: 8px;
    border-radius: 12px;
    border: 1px solid rgba(56, 189, 248, 0.25);
    backdrop-filter: blur(12px);
}
div[data-baseweb="tab"] {
    background-color: transparent !important;
    border-radius: 8px !important;
    color: #94a3b8 !important;
    font-family: 'Orbitron', sans-serif !important;
    font-size: 11px !important;
    transition: all 0.3s ease;
}
div[data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%) !important;
    color: #38bdf8 !important;
    border: 1px solid #38bdf8 !important;
    box-shadow: 0 0 15px rgba(56, 189, 248, 0.6);
}

/* Glowing Neon Buttons with Holographic Gradient */
.stButton > button {
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4c1d95 100%);
    color: #38bdf8;
    border: 1px solid #818cf8;
    border-radius: 8px;
    font-family: 'Orbitron', sans-serif;
    font-size: 13px;
    box-shadow: 0 0 15px rgba(129, 140, 248, 0.35);
    transition: all 0.3s ease;
}
.stButton > button:hover {
    box-shadow: 0 0 28px rgba(56, 189, 248, 0.8);
    border-color: #38bdf8;
    color: #ffffff;
    transform: translateY(-2px);
}

/* Radar Pulse Animation Keyframes */
@keyframes radar-pulse {
    0% { transform: scale(0.95); opacity: 0.8; }
    50% { transform: scale(1.3); opacity: 1; box-shadow: 0 0 15px #4ade80; }
    100% { transform: scale(0.95); opacity: 0.8; }
}
.radar-beacon {
    display: inline-block;
    width: 8px;
    height: 8px;
    background-color: #4ade80;
    border-radius: 50%;
    animation: radar-pulse 1.8s infinite ease-in-out;
    margin-right: 6px;
}

/* Equalizer Bars Keyframes */
@keyframes eq-bar {
    0%, 100% { height: 4px; }
    50% { height: 16px; }
}
.eq-container {
    display: inline-flex;
    align-items: flex-end;
    gap: 2px;
    height: 16px;
    margin-left: 8px;
}
.eq-bar {
    width: 3px;
    background: linear-gradient(to top, #38bdf8, #c084fc);
    animation: eq-bar 0.8s infinite ease-in-out;
    border-radius: 2px;
}
.eq-bar:nth-child(1) { animation-delay: 0.1s; }
.eq-bar:nth-child(2) { animation-delay: 0.3s; }
.eq-bar:nth-child(3) { animation-delay: 0.2s; }
.eq-bar:nth-child(4) { animation-delay: 0.4s; }

/* Padding adjustments */
.block-container {
    padding-top: 2rem !important;
}
</style>
"""
st.markdown(futuristic_style, unsafe_allow_html=True)

# --- SCI-FI UI SOUND FX (JS INTEGRATION) ---
cyber_js = """
<script>
const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
function playSciFiClick() {
    if (audioCtx.state === 'suspended') { audioCtx.resume(); }
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(850, audioCtx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(450, audioCtx.currentTime + 0.05);
    gain.gain.setValueAtTime(0.04, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.05);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + 0.05);
}

document.addEventListener('click', (e) => {
    if (e.target.tagName === 'BUTTON' || e.target.getAttribute('role') === 'tab') {
        playSciFiClick();
    }
});
</script>
"""
components.html(cyber_js, height=0, width=0)

# --- BROWSER-BASED PERSISTENT LOGIN HANDLER ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_name" not in st.session_state:
    st.session_state.user_name = ""

login_sync_js = """
<script>
    const savedName = localStorage.getItem("muk_ai_user_name");
    if (savedName && savedName.trim() !== "") {
        const url = new URL(window.location.href);
        if (!url.searchParams.has("user")) {
            url.searchParams.set("user", savedName);
            window.location.href = url.href;
        }
    }
</script>
"""
components.html(login_sync_js, height=0, width=0)

query_params = st.query_params
if "user" in query_params and query_params["user"]:
    st.session_state.user_name = query_params["user"]
    st.session_state.logged_in = True

# Login Screen if not logged in
if not st.session_state.logged_in:
    st.title("🤖 Welcome to Muk AI")
    st.markdown("### Please sign in to access the world's most beautiful AI assistant")
    
    login_tab1, login_tab2 = st.tabs(["🔴 Sign in with Google", "✍️ Manual Sign In"])
    
    with login_tab1:
        st.write("Sign in instantly using your Google account profile.")
        google_email = st.text_input("Enter your Google Email", placeholder="e.g., student@gmail.com", key="g_email")
        if st.button("Continue with Google"):
            if google_email.strip():
                name_part = google_email.split('@')[0].replace('.', ' ').title()
                st.session_state.user_name = name_part
                st.session_state.logged_in = True
                
                save_js = f"""
                <script>
                    localStorage.setItem("muk_ai_user_name", "{name_part}");
                    const url = new URL(window.location.href);
                    url.searchParams.set("user", "{name_part}");
                    window.location.href = url.href;
                </script>
                """
                components.html(save_js, height=0, width=0)
                st.rerun()
            else:
                st.warning("⚠️ Please enter your Google email address.")
                
    with login_tab2:
        with st.form("login_form"):
            first_name = st.text_input("Your First Name")
            surname = st.text_input("Your Surname")
            submitted = st.form_submit_button("Log In")
            if submitted:
                if first_name.strip() and surname.strip():
                    full_name = f"{first_name.strip()} {surname.strip()}"
                    st.session_state.user_name = full_name
                    st.session_state.logged_in = True
                    
                    save_js = f"""
                    <script>
                        localStorage.setItem("muk_ai_user_name", "{full_name}");
                        const url = new URL(window.location.href);
                        url.searchParams.set("user", "{full_name}");
                        window.location.href = url.href;
                    </script>
                    """
                    components.html(save_js, height=0, width=0)
                    st.rerun()
                else:
                    st.warning("⚠️ Please enter both your name and surname to continue.")
    st.stop()

# Greeting the user + Logout Button in Sidebar
st.title(f"Hello, {st.session_state.user_name}!")
st.markdown("Your ultimate assistant with Aurora Borealis Gradients, Sound FX, and Holographic HUD!")

if st.sidebar.button("🚪 Log Out"):
    st.session_state.logged_in = False
    st.session_state.user_name = ""
    st.query_params.clear()
    clear_js = """
    <script>
        localStorage.removeItem("muk_ai_user_name");
        const url = new URL(window.location.href);
        url.searchParams.delete("user");
        window.location.href = url.origin + url.pathname;
    </script>
    """
    components.html(clear_js, height=0, width=0)
    st.rerun()

# API Key backend configuration via Streamlit Secrets
api_key = None
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("⚠️ GEMINI_API_KEY not found in Streamlit Secrets! Please add your key in your Streamlit Cloud settings.")

client = None
if api_key:
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        st.error(f"Configuration error: {e}")

# Initialize Global History
if "global_history" not in st.session_state:
    st.session_state.global_history = []

# --- HUD TELEMETRY PANEL WITH EQUALIZER & RADAR IN SIDEBAR ---
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="background: rgba(13, 19, 38, 0.85); border: 1px solid #38bdf8; border-radius: 8px; padding: 12px; font-family: 'Share Tech Mono', monospace; font-size: 11px; color: #38bdf8; box-shadow: 0 0 15px rgba(56, 189, 248, 0.25);">
    <b>⚡ HUD TELEMETRY</b>
    <div class="eq-container">
        <div class="eq-bar"></div>
        <div class="eq-bar"></div>
        <div class="eq-bar"></div>
        <div class="eq-bar"></div>
    </div><br>
    • CORE: <span class="radar-beacon"></span><span style="color: #4ade80;">ONLINE</span><br>
    • MODEL: GEMINI-FLASH<br>
    • AESTHETIC: ULTRA-HOLO<br>
    • QUERIES: {}
</div>
""".format(len(st.session_state.global_history)), unsafe_allow_html=True)

# Sidebar Language Switcher
st.sidebar.markdown("---")
st.sidebar.subheader("🌐 Language Settings")
selected_language = st.sidebar.selectbox("Choose Language / Ընտրել լեզուն", ["English", "Հայերեն", "Русский"])

# Sidebar Voice Settings Toggle
st.sidebar.markdown("---")
st.sidebar.subheader("🔊 Audio Settings")
enable_natural_voice = st.sidebar.toggle("Enable Natural Voice 🔊", value=True)

# Sidebar History Log Display
st.sidebar.markdown("---")
st.sidebar.subheader("📜 Recent History")
if st.session_state.global_history:
    for idx, past_item in enumerate(reversed(st.session_state.global_history[-6:])):
        st.sidebar.caption(f"{idx+1}. {past_item}")
    if st.sidebar.button("Clear History"):
        st.session_state.global_history = []
        st.rerun()
else:
    st.sidebar.write("No questions asked yet.")

# Voice synthesizer
def speak_natural_voice(text_to_speak):
    if enable_natural_voice:
        clean_text = text_to_speak.replace('"', "'").replace('\n', ' ')
        js_code = f"""
        <script>
            if ('speechSynthesis' in window) {{
                window.speechSynthesis.cancel();
                const utterance = new SpeechSynthesisUtterance("{clean_text}");
                utterance.pitch = 1.0;
                utterance.rate = 1.0;
                window.speechSynthesis.speak(utterance);
            }}
        </script>
        """
        components.html(js_code, height=0, width=0)

SYSTEM_INSTRUCTION = f"""
You are Muk AI, a multi-functional AI assistant. 
1. If any user asks who created you, who made you, or about your creator, you MUST answer exactly: 'My AI created by Simonyan Mikayel from Armenia'.
2. Always formulate all your output responses in the following language: {selected_language}.
"""

# Navigation Tabs (13 tabs total)
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12, tab13 = st.tabs([
    "📚 Homework", 
    "✍️ Essay", 
    "🔍 Verifier", 
    "📊 Presentation", 
    "🎨 Visuals", 
    "💬 Muk Chat",
    "🧮 Calculator",
    "🧠 Exam Prep",
    "🔤 Translator",
    "📅 Study Planner",
    "🧪 Science & STEM",
    "✉️ Email Writer",
    "💡 Idea Lab"
])

def safe_generate(client_obj, contents):
    models_to_try = ["gemini-3.8-flash", "gemini-2.5-flash", "gemini-1.5-flash"]
    last_error = None
    config = types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
    
    for model_id in models_to_try:
        for attempt in range(3):
            try:
                response = client_obj.models.generate_content(
                    model=model_id, 
                    contents=contents,
                    config=config
                )
                return response
            except Exception as err:
                last_error = err
                err_msg = str(err).lower()
                if "503" in err_msg or "unavailable" in err_msg or "429" in err_msg or "resource_exhausted" in err_msg:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                else:
                    break
    raise last_error

def safe_generate_image(client_obj, prompt_text):
    models_to_try = ["gemini-3.8-flash", "gemini-2.5-flash"]
    last_error = None
    config = types.GenerateContentConfig(
        response_modalities=["IMAGE", "TEXT"],
        system_instruction=SYSTEM_INSTRUCTION
    )
    
    for model_id in models_to_try:
        for attempt in range(3):
            try:
                response = client_obj.models.generate_content(
                    model=model_id,
                    contents=f"Generate a high quality detailed image based on this description: {prompt_text}",
                    config=config
                )
                return response
            except Exception as err:
                last_error = err
                err_msg = str(err).lower()
                if "503" in err_msg or "unavailable" in err_msg or "429" in err_msg or "resource_exhausted" in err_msg:
                    time.sleep(2 * (attempt + 1))
                    continue
                else:
                    break
    raise last_error

def extract_pdf_text(uploaded_pdf):
    reader = PdfReader(uploaded_pdf)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text

def create_pptx_deck(topic, text_content):
    prs = Presentation()
    title_slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(title_slide_layout)
    title = slide.shapes.title
    subtitle = slide.placeholders[1]
    title.text = topic
    subtitle.text = "Generated by Muk AI - Created by Simonyan Mikayel"

    bullet_slide_layout = prs.slide_layouts[1]
    lines = text_content.split('\n')
    current_slide = None
    tf = None

    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
        if "Slide " in line_clean or line_clean.startswith("#") or line_clean.startswith("Title:"):
            current_slide = prs.slides.add_slide(bullet_slide_layout)
            shapes = current_slide.shapes
            title_shape = shapes.title
            title_shape.text = line_clean.replace("#", "").replace("Slide ", "").strip()
            body_shape = shapes.placeholders[1]
            tf = body_shape.text_frame
        elif tf:
            p = tf.add_paragraph()
            p.text = line_clean

    output = BytesIO()
    prs.save(output)
    output.seek(0)
    return output.getvalue()

def create_image_pdf(image_bytes, prompt_text):
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=22, leading=26, textColor='#1E3A8A', spaceAfter=15)
    desc_style = ParagraphStyle('DescStyle', parent=styles['Normal'], fontSize=12, leading=16, spaceAfter=20)
    
    elements = []
    elements.append(Paragraph("<b>Muk AI - Generated Visual Asset</b>", title_style))
    elements.append(Paragraph(f"<b>Prompt Description:</b> {prompt_text}", desc_style))
    elements.append(Spacer(1, 10))
    
    img_temp = BytesIO(image_bytes)
    rl_img = RLImage(img_temp, width=450, height=450)
    elements.append(rl_img)
    
    doc.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()

# --- TAB 1: HOMEWORK HELPER ---
with tab1:
    st.header("Homework Helper")
    st.write("Ask questions by typing, uploading an image/PDF document, or recording your voice!")
    homework_query = st.text_area("What is your homework question?", placeholder="e.g., Solve 3x + 5 = 20 or explain this diagram.", key="hw_q")
    
    col1, col2 = st.columns(2)
    with col1:
        uploaded_hw_image = st.file_uploader("Upload Homework Image or PDF", type=["png", "jpg", "jpeg", "pdf"], key="hw_img")
    with col2:
        audio_hw_input = st.audio_input("Record Voice Question", key="hw_audio")
        
    if uploaded_hw_image and uploaded_hw_image.type != "application/pdf":
        st.image(uploaded_hw_image, caption="Uploaded Homework Image", width=250)
    
    if st.button("Solve Homework"):
        if not client:
            st.error("API client not initialized.")
        else:
            with st.spinner("Muk AI is analyzing your input..."):
                try:
                    payload = []
                    pdf_text = ""
                    if uploaded_hw_image and uploaded_hw_image.type == "application/pdf":
                        pdf_text = extract_pdf_text(uploaded_hw_image)
                    
                    query_text = homework_query if homework_query else "Homework image/audio/PDF analysis"
                    prompt = f"Act as an expert tutor. Solve this homework question step-by-step: {homework_query}\n"
                    if pdf_text:
                        prompt += f"\nExtracted Document Content:\n{pdf_text[:3000]}"
                        
                    payload.append(prompt)
                    if uploaded_hw_image and uploaded_hw_image.type != "application/pdf":
                        payload.append(Image.open(uploaded_hw_image))
                    if audio_hw_input:
                        payload.append(types.Part.from_bytes(data=audio_hw_input.getvalue(), mime_type="audio/wav"))
                    
                    response = safe_generate(client, payload)
                    solution_text = response.text
                    st.session_state.global_history.append(f"Homework: {query_text[:40]}...")
                    st.success("Solution:")
                    st.write(solution_text)
                    speak_natural_voice(solution_text[:300])
                    st.download_button(label="📥 Download Solution as Text File", data=solution_text, file_name="muk_ai_homework_solution.txt", mime="text/plain", key="dl_hw")
                except Exception as e:
                    st.error(f"Error: {e}")

# --- TAB 2: ESSAY WRITER ---
with tab2:
    st.header("Essay & Text Writer")
    st.write("Generate well-structured essays, paragraphs, or summaries.")
    essay_topic = st.text_input("Essay Topic / Prompt", placeholder="e.g., The importance of renewable energy", key="essay_top")
    essay_length = st.selectbox("Length", ["Short paragraph", "Standard Essay (3 paragraphs)", "Detailed Essay"], key="essay_len")
    
    if st.button("Write Essay"):
        if not client:
            st.error("API client not initialized.")
        elif essay_topic:
            with st.spinner("Muk AI is writing..."):
                try:
                    prompt = f"Write a {essay_length.lower()} about: {essay_topic}. Keep it clear, engaging, and well-structured."
                    response = safe_generate(client, prompt)
                    essay_text = response.text
                    st.session_state.global_history.append(f"Essay: {essay_topic[:40]}")
                    st.success("Generated Text:")
                    st.write(essay_text)
                    speak_natural_voice("Your essay has been generated successfully!")
                    st.download_button(label="📥 Download Essay as Text File", data=essay_text, file_name="muk_ai_essay.txt", mime="text/plain", key="dl_essay")
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Please enter a topic.")

# --- TAB 3: ANSWER VERIFIER ---
with tab3:
    st.header("Answer Verifier")
    st.write("Check your answers or verify text generated from other AIs to make sure they are accurate.")
    question_to_verify = st.text_input("Original Question", placeholder="e.g., What is the capital of Australia?", key="ver_q")
    answer_to_verify = st.text_area("Answer to Verify", placeholder="Paste the answer here...", key="ver_a")
    verify_image = st.file_uploader("Upload Answer Image or PDF (optional)", type=["png", "jpg", "jpeg", "pdf"], key="ver_img")
    
    if st.button("Verify Answer"):
        if not client:
            st.error("API client not initialized.")
        elif question_to_verify or answer_to_verify or verify_image:
            with st.spinner("Muk AI is verifying..."):
                try:
                    pdf_text = ""
                    if verify_image and verify_image.type == "application/pdf":
                        pdf_text = extract_pdf_text(verify_image)
                    
                    prompt = f"Verify the following answer for accuracy. Question: {question_to_verify}\nAnswer to check: {answer_to_verify}"
                    if pdf_text:
                        prompt += f"\nDocument Context:\n{pdf_text[:3000]}"
                        
                    payload = [prompt]
                    if verify_image and verify_image.type != "application/pdf":
                        payload.append(Image.open(verify_image))
                        
                    response = safe_generate(client, payload)
                    st.session_state.global_history.append(f"Verify: {question_to_verify[:40] if question_to_verify else 'Document'}")
                    st.success("Verification Report:")
                    st.write(response.text)
                    speak_natural_voice("Verification report is ready!")
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Please provide details or a file to verify.")

# --- TAB 4: PRESENTATION MAKER ---
with tab4:
    st.header("📊 Presentation Maker")
    st.write("Generate complete presentations and download them as text or actual PowerPoint (.pptx) files!")
    pres_topic = st.text_input("Presentation Topic", placeholder="e.g., History of Space Exploration or AI", key="pres_top")
    pres_slides = st.slider("Number of Slides", min_value=0, max_value=20, value=10)
    
    if st.button("Generate Presentation Deck"):
        if not client:
            st.error("API client not initialized.")
        elif pres_slides == 0:
            st.warning("⚠️ Please select at least 1 slide.")
        elif pres_topic:
            with st.spinner("Designing presentation deck..."):
                try:
                    prompt = f"Create a professional {pres_slides}-slide presentation outline on: {pres_topic}. Include slide titles and clear bullet points for each slide."
                    response = safe_generate(client, prompt)
                    pres_text = response.text
                    st.session_state.global_history.append(f"Presentation: {pres_topic[:40]}")
                    st.success("Presentation Deck Outline:")
                    st.write(pres_text)
                    speak_natural_voice("Your presentation deck is ready!")
                    
                    col_d1, col_d2 = st.columns(2)
                    with col_d1:
                        st.download_button(label="📥 Download Outline (.txt)", data=pres_text, file_name="muk_ai_presentation.txt", mime="text/plain", key="dl_pres")
                    with col_d2:
                        pptx_data = create_pptx_deck(pres_topic, pres_text)
                        st.download_button(label="📊 Download PowerPoint (.pptx)", data=pptx_data, file_name="muk_ai_presentation.pptx", mime="application/vnd.openxmlformats-officedocument.presentationml.presentation", key="dl_pres_pptx")
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Please enter a presentation topic.")

# --- TAB 5: VISUALS (PICTURE & VIDEO CREATOR) ---
with tab5:
    st.header("🎨 Picture & Video Creator")
    st.write("Generate stunning images and download them as high-quality PDF assets!")
    img_prompt = st.text_input("Image Description / Prompt", placeholder="e.g., A futuristic cyberpunk city in Armenia, digital art", key="img_prompt_input")
    
    if st.button("Generate Visual"):
        if not client:
            st.error("API client not initialized.")
        elif img_prompt:
            with st.spinner("Muk AI is painting your visual..."):
                try:
                    response = safe_generate_image(client, img_prompt)
                    image_found = False
                    if response.candidates:
                        for candidate in response.candidates:
                            if candidate.content and candidate.content.parts:
                                for part in candidate.content.parts:
                                    if part.inline_data:
                                        img_bytes = part.inline_data.data
                                        image = Image.open(BytesIO(img_bytes))
                                        st.image(image, caption=img_prompt, use_column_width=True)
                                        image_found = True
                                        st.session_state.global_history.append(f"Visual: {img_prompt[:40]}")
                                        speak_natural_voice("Your image has been generated!")
                                        
                                        pdf_data = create_image_pdf(img_bytes, img_prompt)
                                        st.download_button(
                                            label="📥 Download Image as PDF Asset",
                                            data=pdf_data,
                                            file_name="muk_ai_visual.pdf",
                                            mime="application/pdf",
                                            key="dl_vis_pdf"
                                        )
                                        break
                    if not image_found:
                        st.warning("Model returned text response instead of image:")
                        st.write(response.text)
                except Exception as e:
                    st.error(f"Image generation error: {e}")
        else:
            st.warning("Please enter a description for your image.")

# --- TAB 6: MUK CHAT ---
with tab6:
    st.header("💬 Muk AI Chat")
    st.write("Chat freely with your personal AI assistant.")
    
    web_search_toggle = st.toggle("🌐 Enable Web Research Mode", value=False)
    
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
        
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
    if chat_input := st.chat_input("Ask Muk AI anything..."):
        st.session_state.chat_messages.append({"role": "user", "content": chat_input})
        with st.chat_message("user"):
            st.markdown(chat_input)
            
        if client:
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        history_payload = []
                        if web_search_toggle:
                            history_payload.append("System Notice: Provide up-to-date, comprehensive, well-researched web answers with citations where appropriate.")
                        for m in st.session_state.chat_messages:
                            history_payload.append(f"{m['role'].capitalize()}: {m['content']}")
                        response = safe_generate(client, history_payload)
                        reply = response.text
                        st.markdown(reply)
                        st.session_state.chat_messages.append({"role": "assistant", "content": reply})
                        st.session_state.global_history.append(f"Chat: {chat_input[:30]}...")
                        speak_natural_voice(reply[:200])
                    except Exception as e:
                        st.error(f"Error: {e}")

# --- TAB 7: CALCULATOR & GRAPHING ---
with tab7:
    st.header("🧮 Smart Calculator & Graph Plotter")
    st.write("Solve math equations or plot mathematical functions visually!")
    
    calc_input = st.text_input("Enter math expression or function to plot", placeholder="e.g., plot x^2 - 4 or solve 15% of 340", key="calc_box")
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        calc_btn = st.button("Calculate & Explain")
    with col_c2:
        plot_btn = st.button("📈 Plot Graph (x^2, sin(x), etc.)")
        
    if calc_btn:
        if not client:
            st.error("API client not initialized.")
        elif calc_input:
            with st.spinner("Calculating..."):
                try:
                    prompt = f"Calculate the answer and provide step-by-step working for: {calc_input}"
                    response = safe_generate(client, prompt)
                    calc_result = response.text
                    st.session_state.global_history.append(f"Calculator: {calc_input[:30]}")
                    st.success("Result:")
                    st.write(calc_result)
                    speak_natural_voice("Calculation complete!")
                except Exception as e:
                    st.error(f"Error: {e}")
                    
    if plot_btn:
        if calc_input:
            try:
                x = np.linspace(-10, 10, 400)
                expr = calc_input.replace("plot", "").replace("^", "**").replace("sin", "np.sin").replace("cos", "np.cos").strip()
                y = eval(expr, {"x": x, "np": np})
                
                fig, ax = plt.subplots()
                ax.plot(x, y, color="#38bdf8", linewidth=2)
                ax.set_title(f"Graph of {calc_input}", color="white")
                ax.grid(True, linestyle="--", alpha=0.5)
                fig.patch.set_facecolor('#090d1a')
                ax.set_facecolor('#050711')
                ax.tick_params(colors='white')
                ax.xaxis.label.set_color('white')
                ax.yaxis.label.set_color('white')
                
                st.pyplot(fig)
                st.session_state.global_history.append(f"Graph: {calc_input[:30]}")
            except Exception as e:
                st.error(f"Could not plot expression: {e}. Try entering a formula with 'x', e.g., 'x**2' or 'sin(x)'.")

# --- TAB 8: EXAM PREP (QUIZZES & FLASHCARDS) ---
with tab8:
    st.header("🧠 Study & Exam Prep Mode")
    st.write("Generate interactive practice quizzes and digital flashcards from any topic or study notes!")
    
    study_topic = st.text_area("Enter study notes, textbook text, or topic name", placeholder="e.g., Photosynthesis, World War II history, or paste your class notes here...", key="study_input")
    study_mode = st.radio("Choose Mode", ["Multiple Choice Quiz", "Digital Flashcards Deck"], horizontal=True)
    
    if st.button("Generate Exam Practice"):
        if not client:
            st.error("API client not initialized.")
        elif study_topic:
            with st.spinner("Muk AI is generating your study material..."):
                try:
                    if study_mode == "Multiple Choice Quiz":
                        prompt = f"Create a 5-question multiple choice quiz with answer key based on: {study_topic}."
                    else:
                        prompt = f"Create a set of 5 digital flashcards with 'Front (Question)' and 'Back (Answer)' based on: {study_topic}."
                        
                    response = safe_generate(client, prompt)
                    st.session_state.global_history.append(f"Exam Prep: {study_topic[:30]}")
                    st.success("Study Material Ready:")
                    st.write(response.text)
                    speak_natural_voice("Your exam practice materials are ready!")
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Please enter a topic or paste study notes.")

# --- TAB 9: SMART MULTILINGUAL TRANSLATOR ---
with tab9:
    st.header("🔤 Contextual Multilingual Translator")
    st.write("Translate text while preserving context, idioms, and natural speaking tone.")
    
    trans_text = st.text_input("Enter text to translate", placeholder="e.g., How are you doing today?", key="trans_box")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        src_lang = st.selectbox("From Language", ["Auto-Detect", "English", "Armenian", "Russian"], key="src_lang")
    with col_t2:
        target_lang = st.selectbox("To Language", ["Armenian", "English", "Russian", "French", "German", "Spanish"], key="target_lang")
        
    if st.button("Translate with Context"):
        if not client:
            st.error("API client not initialized.")
        elif trans_text:
            with st.spinner("Translating..."):
                try:
                    prompt = f"Translate the following text from {src_lang} to {target_lang}. Preserve exact natural context and explain any idioms or cultural nuances if present: {trans_text}"
                    response = safe_generate(client, prompt)
                    st.session_state.global_history.append(f"Translation: {trans_text[:30]}")
                    st.success("Translation:")
                    st.write(response.text)
                    speak_natural_voice(response.text[:300])
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Please enter text to translate.")

# --- TAB 10: DAILY STUDY PLANNER ---
with tab10:
    st.header("📅 Daily Study Planner & Schedule Creator")
    st.write("Generate customized study schedules tailored to your exams and available daily time.")
    
    subjects = st.text_input("Enter Subjects/Topics to study", placeholder="e.g., Math, Physics, Armenian History", key="plan_subjs")
    days_left = st.number_input("Days until exam/deadline", min_value=1, max_value=60, value=7)
    daily_hours = st.slider("Free study hours per day", min_value=1, max_value=10, value=3)
    
    if st.button("Create Study Schedule"):
        if not client:
            st.error("API client not initialized.")
        elif subjects:
            with st.spinner("Building custom study timetable..."):
                try:
                    prompt = f"Create a structured, day-by-day study schedule for the next {days_left} days covering these subjects: {subjects}. The student has {daily_hours} hours available each day. Include specific study goals and break periods."
                    response = safe_generate(client, prompt)
                    st.session_state.global_history.append(f"Planner: {subjects[:30]}")
                    st.success("Your Personalized Timetable:")
                    st.write(response.text)
                    speak_natural_voice("Your study schedule is ready!")
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Please enter your subjects or topics.")

# --- TAB 11: SCIENCE & STEM ASSISTANT ---
with tab11:
    st.header("🧪 Science & Physics STEM Assistant")
    st.write("Understand complex physics, chemistry, or biology formulas with step-by-step real-world explanations.")
    
    stem_concept = st.text_input("Enter Science Question or Formula", placeholder="e.g., Explain Newton's Second Law F=ma or Photosynthesis", key="stem_box")
    
    if st.button("Explain Science Concept"):
        if not client:
            st.error("API client not initialized.")
        elif stem_concept:
            with st.spinner("Analyzing scientific concept..."):
                try:
                    prompt = f"Act as an expert STEM tutor. Explain this science concept or formula step-by-step with real-world examples, formula breakdown, and intuitive analogies: {stem_concept}"
                    response = safe_generate(client, prompt)
                    st.session_state.global_history.append(f"STEM: {stem_concept[:30]}")
                    st.success("Scientific Breakdown:")
                    st.write(response.text)
                    speak_natural_voice("Scientific explanation complete!")
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Please enter a science question or formula.")

# --- TAB 12: PROFESSIONAL EMAIL WRITER ---
with tab12:
    st.header("✉️ Professional Email & Letter Writer")
    st.write("Draft polite, well-phrased emails and formal requests instantly.")
    
    email_purpose = st.text_input("Main Purpose of Email", placeholder="e.g., Asking teacher for extra deadline time or sending job application", key="email_purp")
    email_tone = st.selectbox("Tone", ["Formal / Professional", "Friendly / Polite", "Persuasive"], key="email_tone")
    
    if st.button("Draft Email"):
        if not client:
            st.error("API client not initialized.")
        elif email_purpose:
            with st.spinner("Drafting email..."):
                try:
                    prompt = f"Draft a complete, well-structured email with Subject line and Body. Tone should be {email_tone}. Purpose: {email_purpose}"
                    response = safe_generate(client, prompt)
                    st.session_state.global_history.append(f"Email: {email_purpose[:30]}")
                    st.success("Drafted Email:")
                    st.write(response.text)
                    speak_natural_voice("Your email draft is ready!")
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Please enter the main purpose of your email.")

# --- TAB 13: CREATIVE IDEA GENERATOR ---
with tab13:
    st.header("💡 Brainstorming & Idea Generator")
    st.write("Generate creative concepts for video projects, presentations, essays, or apps.")
    
    idea_topic = st.text_input("What do you want ideas for?", placeholder="e.g., Creative video topic about sea painting or web app idea", key="idea_box")
    
    if st.button("Generate Creative Ideas"):
        if not client:
            st.error("API client not initialized.")
        elif idea_topic:
            with st.spinner("Brainstorming creative ideas..."):
                try:
                    prompt = f"Generate 5 unique, creative, and engaging project ideas or concepts for: {idea_topic}. Include a title, brief description, and key highlight for each idea."
                    response = safe_generate(client, prompt)
                    st.session_state.global_history.append(f"Idea Lab: {idea_topic[:30]}")
                    st.success("Creative Concepts:")
                    st.write(response.text)
                    speak_natural_voice("Here are your creative ideas!")
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Please enter a topic to generate ideas.")

# --- BRANDING AT THE VERY BOTTOM OF THE SIDEBAR ---
st.sidebar.markdown("---")
st.sidebar.markdown("<p style='font-size: 12px; color: #f8fafc; text-align: center;'>My AI created by Simonyan Mikayel from Armenia</p>", unsafe_allow_html=True)
