import time
from io import BytesIO
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
from google import genai
from google.genai import types

# ReportLab libraries for generating PDFs
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# Configure Muk AI Page with expanded sidebar by default
st.set_page_config(
    page_title="Muk AI - Ultimate AI Assistant",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- FUTURISTIC CYBERPUNK & SIDEBAR VISIBILITY STYLING ---
futuristic_style = """
<style>
/* Dark Sci-Fi Cyberpunk Background */
.stApp {
    background-color: #0b0f19;
    color: #e2e8f0;
}

/* Glassmorphism Sidebar with Guaranteed Text Visibility */
section[data-testid="stSidebar"] {
    background-color: #0f172a;
    border-right: 1px solid #1e293b;
}

section[data-testid="stSidebar"] p, 
section[data-testid="stSidebar"] span, 
section[data-testid="stSidebar"] label, 
section[data-testid="stSidebar"] h1, 
section[data-testid="stSidebar"] h2, 
section[data-testid="stSidebar"] h3 {
    color: #f8fafc !important;
}

/* Glowing Neon Accent Buttons */
.stButton > button {
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
    color: #38bdf8;
    border: 1px solid #6366f1;
    border-radius: 8px;
    box-shadow: 0 0 10px rgba(99, 102, 241, 0.3);
    transition: all 0.3s ease;
}

.stButton > button:hover {
    box-shadow: 0 0 20px rgba(56, 189, 248, 0.6);
    border-color: #38bdf8;
    color: #ffffff;
}

/* Padding adjustments */
.block-container {
    padding-top: 2rem !important;
}
</style>
"""
st.markdown(futuristic_style, unsafe_allow_html=True)

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

# Check URL query params for auto-restore after refresh
query_params = st.query_params
if "user" in query_params and query_params["user"]:
    st.session_state.user_name = query_params["user"]
    st.session_state.logged_in = True

# Login Screen if not logged in
if not st.session_state.logged_in:
    st.title("🤖 Welcome to Muk AI")
    st.markdown("### Please sign in to access your AI assistant")
    
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
st.markdown("Your ultimate assistant with Text, Image & PDF Generation, Voice, and History tracking!")

# Add Logout button to Sidebar
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

# Navigation Tabs (7 tabs)
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📚 Homework", 
    "✍️ Essay", 
    "🔍 Verifier", 
    "📊 Presentation", 
    "🎨 Visuals", 
    "💬 Muk Chat",
    "🧮 Calculator"
])

def safe_generate(client_obj, contents):
    models_to_try = [
        "gemini-3.8-flash"
    ]
    last_error = None
    config = types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
    
    for model_id in models_to_try:
        for attempt in range(2):
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
                if "404" in err_msg or "not_found" in err_msg or "429" in err_msg or "resource_exhausted" in err_msg:
                    break
                if "503" in err_msg or "unavailable" in err_msg:
                    time.sleep(1.5)
                    continue
                else:
                    break
    raise last_error

def safe_generate_image(client_obj, prompt_text):
    models_to_try = [
        "gemini-3.8-flash"
    ]
    last_error = None
    config = types.GenerateContentConfig(
        response_modalities=["IMAGE", "TEXT"],
        system_instruction=SYSTEM_INSTRUCTION
    )
    
    for model_id in models_to_try:
        for attempt in range(2):
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
                    time.sleep(2)
                    continue
                else:
                    break
    raise last_error

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
    st.write("Ask questions by typing, uploading an image of your exercise, or recording your voice!")
    homework_query = st.text_area("What is your homework question?", placeholder="e.g., Solve 3x + 5 = 20 or explain this diagram.", key="hw_q")
    col1, col2 = st.columns(2)
    with col1:
        uploaded_hw_image = st.file_uploader("Upload Homework Image", type=["png", "jpg", "jpeg"], key="hw_img")
    with col2:
        audio_hw_input = st.audio_input("Record Voice Question", key="hw_audio")
        
    if uploaded_hw_image:
        st.image(uploaded_hw_image, caption="Uploaded Homework Image", width=250)
    
    if st.button("Solve Homework"):
        if not client:
            st.error("API client not initialized.")
        else:
            with st.spinner("Muk AI is analyzing your input..."):
                try:
                    payload = []
                    query_text = homework_query if homework_query else "Homework image/audio analysis"
                    if homework_query:
                        payload.append(f"Act as an expert tutor. Solve this homework question step-by-step: {homework_query}")
                    else:
                        payload.append("Act as an expert tutor. Solve the homework shown in this input step-by-step.")
                    if uploaded_hw_image:
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
    verify_image = st.file_uploader("Upload Answer Image (optional)", type=["png", "jpg", "jpeg"], key="ver_img")
    
    if verify_image:
        st.image(verify_image, width=250)
        
    if st.button("Verify Answer"):
        if not client:
            st.error("API client not initialized.")
        elif question_to_verify or answer_to_verify or verify_image:
            with st.spinner("Muk AI is verifying..."):
                try:
                    payload = [f"Verify the following answer for accuracy. Question: {question_to_verify}\nAnswer to check: {answer_to_verify}"]
                    if verify_image:
                        payload.append(Image.open(verify_image))
                    response = safe_generate(client, payload)
                    st.session_state.global_history.append(f"Verify: {question_to_verify[:40] if question_to_verify else 'Image'}")
                    st.success("Verification Report:")
                    st.write(response.text)
                    speak_natural_voice("Verification report is ready!")
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Please provide details or an image to verify.")

# --- TAB 4: PRESENTATION MAKER ---
with tab4:
    st.header("📊 Presentation Maker")
    st.write("Generate a complete, professional slide-by-slide presentation deck with titles, bullet points, and speaker notes.")
    pres_topic = st.text_input("Presentation Topic", placeholder="e.g., History of Space Exploration or AI", key="pres_top")
    pres_slides = st.slider("Number of Slides", min_value=0, max_value=20, value=10)
    
    if st.button("Generate Presentation Outline"):
        if not client:
            st.error("API client not initialized.")
        elif pres_slides == 0:
            st.warning("⚠️ Please select at least 1 slide.")
        elif pres_topic:
            with st.spinner("Designing presentation deck..."):
                try:
                    prompt = f"Create a professional {pres_slides}-slide presentation outline on: {pres_topic}. Include slide titles, bullet points, and speaker notes for each slide."
                    response = safe_generate(client, prompt)
                    pres_text = response.text
                    st.session_state.global_history.append(f"Presentation: {pres_topic[:40]}")
                    st.success("Presentation Deck Outline:")
                    st.write(pres_text)
                    speak_natural_voice("Your presentation outline is ready!")
                    st.download_button(label="📥 Download Presentation Outline as Text", data=pres_text, file_name="muk_ai_presentation.txt", mime="text/plain", key="dl_pres")
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
            with st.spinner("Muk AI is painting your visual (with automatic fallback)..."):
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

# --- TAB 7: CALCULATOR ---
with tab7:
    st.header("🧮 Smart Calculator")
    st.write("Solve complex math equations, word problems, or scientific calculations step-by-step.")
    calc_input = st.text_input("Enter math expression or word problem", placeholder="e.g., What is the integral of x^2 or calculate 15% of 340", key="calc_box")
    
    if st.button("Calculate & Explain"):
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
        else:
            st.warning("Please enter a math expression.")

# --- BRANDING AT THE VERY BOTTOM OF THE SIDEBAR ---
st.sidebar.markdown("---")
st.sidebar.markdown("<p style='font-size: 12px; color: #f8fafc; text-align: center;'>My AI created by Simonyan Mikayel from Armenia</p>", unsafe_allow_html=True)
