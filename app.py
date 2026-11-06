import time
import uuid
import smtplib
from email.message import EmailMessage
import sqlite3
import bcrypt
from io import BytesIO
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
from google import genai
from google.genai import types

from pypdf import PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from pptx import Presentation

import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(
    page_title="Muk AI - Ultimate AI Assistant",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- 1. DATABASE SETUP (USERS, HISTORY & RESET TOKENS) ---
def init_db():
    conn = sqlite3.connect("muk_ai_secure.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            email TEXT UNIQUE,
            password_hash BLOB,
            app_passcode TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            history_item TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS reset_tokens (
            token TEXT PRIMARY KEY,
            email TEXT,
            reset_type TEXT,
            expires_at REAL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def create_user(username, email, password, passcode):
    conn = sqlite3.connect("muk_ai_secure.db")
    c = conn.cursor()
    salt = bcrypt.gensalt()
    pw_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    try:
        c.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (username, email.lower(), pw_hash, passcode))
        conn.commit()
        conn.close()
        return True, "Account created successfully! Please log in."
    except sqlite3.IntegrityError as e:
        conn.close()
        if "username" in str(e):
            return False, "Username already exists."
        return False, "Email already registered."

def verify_user(username_or_email, password):
    conn = sqlite3.connect("muk_ai_secure.db")
    c = conn.cursor()
    c.execute("SELECT username, password_hash, app_passcode FROM users WHERE username=? OR email=?", (username_or_email, username_or_email.lower()))
    user = c.fetchone()
    conn.close()
    
    if user and bcrypt.checkpw(password.encode('utf-8'), user[1]):
        return True, user[0], user[2]
    return False, None, None

def get_user_by_email(email):
    conn = sqlite3.connect("muk_ai_secure.db")
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE email=?", (email.lower(),))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def generate_reset_token(email, reset_type):
    token = str(uuid.uuid4())
    expires_at = time.time() + 1800  # Valid for 30 minutes
    conn = sqlite3.connect("muk_ai_secure.db")
    c = conn.cursor()
    c.execute("INSERT INTO reset_tokens VALUES (?, ?, ?, ?)", (token, email.lower(), reset_type, expires_at))
    conn.commit()
    conn.close()
    return token

def validate_reset_token(token):
    conn = sqlite3.connect("muk_ai_secure.db")
    c = conn.cursor()
    c.execute("SELECT email, reset_type, expires_at FROM reset_tokens WHERE token=?", (token,))
    row = c.fetchone()
    conn.close()
    if row and time.time() < row[2]:
        return row[0], row[1]  # email, reset_type
    return None, None

def consume_reset_token(token):
    conn = sqlite3.connect("muk_ai_secure.db")
    c = conn.cursor()
    c.execute("DELETE FROM reset_tokens WHERE token=?", (token,))
    conn.commit()
    conn.close()

def update_user_password(email, new_password):
    conn = sqlite3.connect("muk_ai_secure.db")
    c = conn.cursor()
    salt = bcrypt.gensalt()
    pw_hash = bcrypt.hashpw(new_password.encode('utf-8'), salt)
    c.execute("UPDATE users SET password_hash=? WHERE email=?", (pw_hash, email.lower()))
    conn.commit()
    conn.close()

def update_user_pin(email, new_pin):
    conn = sqlite3.connect("muk_ai_secure.db")
    c = conn.cursor()
    c.execute("UPDATE users SET app_passcode=? WHERE email=?", (new_pin, email.lower()))
    conn.commit()
    conn.close()

def send_recovery_email(to_email, username, token, reset_type):
    smtp_email = st.secrets.get("SMTP_EMAIL", "")
    smtp_password = st.secrets.get("SMTP_PASSWORD", "")
    app_url = st.secrets.get("APP_URL", "http://localhost:8501").rstrip("/")
    
    if not smtp_email or not smtp_password:
        return False, "SMTP_EMAIL or SMTP_PASSWORD is missing in Streamlit Secrets."
        
    reset_link = f"{app_url}/?reset_token={token}"
    label = "Password" if reset_type == "password" else "App PIN / Passcode"
    
    msg = EmailMessage()
    msg["Subject"] = f"Muk AI - Reset Your {label}"
    msg["From"] = f"Muk AI Security <{smtp_email}>"
    msg["To"] = to_email
    
    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #050711; color: #e2e8f0; padding: 30px;">
        <div style="max-width: 500px; margin: auto; background: #0d1326; padding: 25px; border-radius: 12px; border: 1px solid #38bdf8;">
          <h2 style="color: #38bdf8; margin-top: 0;">🤖 Muk AI Security Verification</h2>
          <p>Hello <b>{username}</b>,</p>
          <p>We received a request to reset your <b>{label}</b>. Click the button below to confirm your identity and create a new {label.lower()}:</p>
          <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_link}" style="background: linear-gradient(135deg, #38bdf8, #818cf8); color: #050711; padding: 14px 28px; text-decoration: none; font-weight: bold; border-radius: 8px; display: inline-block;">
              Create New {label}
            </a>
          </div>
          <p style="font-size: 12px; color: #94a3b8;">This link expires in 30 minutes. If you didn't request this, you can safely ignore this email.</p>
        </div>
      </body>
    </html>
    """
    msg.set_content(f"Hello {username}, click this link to reset your {label}: {reset_link}")
    msg.add_alternative(html_body, subtype="html")
    
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(smtp_email, smtp_password)
            server.send_message(msg)
        return True, f"Confirmation email sent to {to_email}! Check your inbox and click the button inside."
    except Exception as e:
        return False, f"Failed to send email: {e}"

def load_user_history(username):
    conn = sqlite3.connect("muk_ai_secure.db")
    c = conn.cursor()
    c.execute("SELECT history_item FROM history WHERE username=?", (username,))
    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows]

def save_user_history_item(username, item):
    conn = sqlite3.connect("muk_ai_secure.db")
    c = conn.cursor()
    c.execute("INSERT INTO history (username, history_item) VALUES (?, ?)", (username, item))
    conn.commit()
    conn.close()

def clear_user_history_db(username):
    conn = sqlite3.connect("muk_ai_secure.db")
    c = conn.cursor()
    c.execute("DELETE FROM history WHERE username=?", (username,))
    conn.commit()
    conn.close()

# --- 2. FUTURISTIC UI STYLING & SOUND FX ---
futuristic_style = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;800&family=Share+Tech+Mono&display=swap');

footer { visibility: hidden !important; }
[data-testid="stStatusWidget"] { display: none !important; }
.stDeployButton { display: none !important; }
div[class*="viewerBadge"] { display: none !important; }

[data-testid="collapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    color: #38bdf8 !important;
    z-index: 999999 !important;
}

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

h1, h2, h3 {
    font-family: 'Orbitron', sans-serif !important;
    background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: 1.5px;
    text-shadow: 0 0 20px rgba(56, 189, 248, 0.3);
}

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

.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"], .stNumberInput input {
    background-color: rgba(13, 19, 38, 0.9) !important;
    border: 1px solid rgba(56, 189, 248, 0.4) !important;
    border-left: 3px solid #38bdf8 !important;
    color: #f8fafc !important;
    border-radius: 6px !important;
    backdrop-filter: blur(8px);
}
.stTextInput input:hover, .stTextArea textarea:hover, .stSelectbox div[data-baseweb="select"]:hover {
    border-color: #c084fc !important;
    box-shadow: 0 0 20px rgba(192, 132, 252, 0.4) !important;
    transform: translateY(-2px);
}

[data-testid="stChatInput"], [data-testid="stChatInput"] div[data-baseweb="base-input"] {
    background-color: rgba(13, 19, 38, 0.95) !important;
    border: 1px solid rgba(56, 189, 248, 0.5) !important;
    border-radius: 8px !important;
    color: #f8fafc !important;
    box-shadow: 0 0 15px rgba(56, 189, 248, 0.25);
}
[data-testid="stChatInput"] textarea {
    background-color: transparent !important;
    color: #f8fafc !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: #94a3b8 !important;
}

div[data-baseweb="tab-list"] {
    display: flex !important;
    visibility: visible !important;
    gap: 8px;
    background: rgba(9, 13, 26, 0.75);
    padding: 8px;
    border-radius: 12px;
    border: 1px solid rgba(56, 189, 248, 0.25);
    backdrop-filter: blur(12px);
    overflow-x: auto !important;
}
div[data-baseweb="tab"] {
    background-color: transparent !important;
    border-radius: 8px !important;
    color: #94a3b8 !important;
    font-family: 'Orbitron', sans-serif !important;
    font-size: 11px !important;
    transition: all 0.3s ease;
    white-space: nowrap !important;
}
div[data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%) !important;
    color: #38bdf8 !important;
    border: 1px solid #38bdf8 !important;
    box-shadow: 0 0 15px rgba(56, 189, 248, 0.6);
}

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

.block-container {
    padding-top: 2rem !important;
}
</style>
"""
st.markdown(futuristic_style, unsafe_allow_html=True)

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

# --- 3. HANDLE MAGIC EMAIL RESET BUTTON LINK (?reset_token=...) ---
query_params = st.query_params
if "reset_token" in query_params and query_params["reset_token"]:
    token = query_params["reset_token"]
    reset_email, reset_type = validate_reset_token(token)
    
    if reset_email and reset_type:
        username = get_user_by_email(reset_email)
        if reset_type == "password":
            st.title("🔐 Create New Password")
            st.markdown(f"### Verified Account: `{username}` ({reset_email})")
            with st.form("new_pw_form"):
                new_pw = st.text_input("Enter New Password", type="password")
                confirm_pw = st.text_input("Confirm New Password", type="password")
                save_pw_btn = st.form_submit_button("Save Password & Log In")
                if save_pw_btn:
                    if len(new_pw) < 6:
                        st.warning("⚠️ Password must be at least 6 characters long.")
                    elif new_pw != confirm_pw:
                        st.error("❌ Passwords do not match.")
                    else:
                        update_user_password(reset_email, new_pw)
                        consume_reset_token(token)
                        st.query_params.clear()
                        st.session_state.user_name = username
                        st.session_state.logged_in = True
                        st.session_state.passcode_verified = True
                        st.success("✅ Password updated! Logging you in...")
                        time.sleep(1)
                        st.rerun()
        elif reset_type == "pin":
            st.title("🔢 Create New App PIN / Passcode")
            st.markdown(f"### Verified Account: `{username}` ({reset_email})")
            with st.form("new_pin_form"):
                new_pin = st.text_input("Enter New 4-6 Digit PIN", type="password", max_chars=6)
                confirm_pin = st.text_input("Confirm New PIN", type="password", max_chars=6)
                save_pin_btn = st.form_submit_button("Save New PIN & Unlock")
                if save_pin_btn:
                    if not new_pin.strip():
                        st.warning("⚠️ Please enter a valid PIN.")
                    elif new_pin != confirm_pin:
                        st.error("❌ PINs do not match.")
                    else:
                        update_user_pin(reset_email, new_pin.strip())
                        consume_reset_token(token)
                        st.query_params.clear()
                        st.session_state.user_name = username
                        st.session_state.logged_in = True
                        st.session_state.passcode_verified = True
                        st.success("✅ App PIN updated! Unlocking your account...")
                        time.sleep(1)
                        st.rerun()
    else:
        st.error("❌ This reset link is invalid or has expired.")
        if st.button("Back to Log In"):
            st.query_params.clear()
            st.rerun()
    st.stop()

# --- 4. SESSION STATE & AUTHENTICATION ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "passcode_verified" not in st.session_state:
    st.session_state.passcode_verified = False

if "user" in query_params and query_params["user"]:
    st.session_state.user_name = query_params["user"]
    st.session_state.logged_in = True

if not st.session_state.logged_in:
    st.title("🤖 Welcome to Muk AI")
    st.markdown("### Secure Sign In, Registration & Account Recovery")
    
    tab_login, tab_signup, tab_forgot_pw = st.tabs(["🔑 Log In", "📝 Sign Up", "❓ Forgot Password"])
    
    with tab_login:
        with st.form("login_form"):
            login_input = st.text_input("Username or Email")
            login_password = st.text_input("Password", type="password")
            btn_login = st.form_submit_button("Log In")
            if btn_login:
                if not login_input.strip() or not login_password.strip():
                    st.warning("⚠️ Please fill in all fields.")
                else:
                    success, username, passcode = verify_user(login_input.strip(), login_password.strip())
                    if success:
                        st.session_state.user_name = username
                        st.session_state.logged_in = True
                        st.session_state.saved_passcode = passcode
                        st.session_state.passcode_verified = False
                        st.rerun()
                    else:
                        st.error("❌ Invalid username/email or password.")
                        
    with tab_signup:
        with st.form("signup_form"):
            new_username = st.text_input("Choose a Username")
            new_email = st.text_input("Email Address")
            new_password = st.text_input("Choose a Password", type="password")
            new_passcode = st.text_input("Set a 4-6 Digit App Passcode / PIN", type="password", max_chars=6, placeholder="e.g. 1234")
            confirm_password = st.text_input("Confirm Password", type="password")
            btn_signup = st.form_submit_button("Create Account")
            if btn_signup:
                if not new_username.strip() or not new_email.strip() or not new_password.strip() or not new_passcode.strip():
                    st.warning("⚠️ Please fill out all required fields including your App Passcode.")
                elif new_password != confirm_password:
                    st.error("❌ Passwords do not match.")
                elif len(new_password) < 6:
                    st.warning("⚠️ Password must be at least 6 characters long.")
                else:
                    created, msg = create_user(new_username.strip(), new_email.strip(), new_password.strip(), new_passcode.strip())
                    if created:
                        st.success(msg)
                    else:
                        st.error(f"❌ {msg}")

    with tab_forgot_pw:
        st.write("Forgot your password? Enter your registered email address and we will send you a confirmation button to create a new password.")
        with st.form("forgot_pw_form"):
            recovery_email = st.text_input("Registered Email Address")
            send_pw_btn = st.form_submit_button("Send Password Reset Email")
            if send_pw_btn:
                if not recovery_email.strip():
                    st.warning("⚠️ Please enter your email address.")
                else:
                    found_user = get_user_by_email(recovery_email.strip())
                    if found_user:
                        token = generate_reset_token(recovery_email.strip(), "password")
                        sent, info_msg = send_recovery_email(recovery_email.strip(), found_user, token, "password")
                        if sent:
                            st.success(info_msg)
                        else:
                            st.error(info_msg)
                    else:
                        st.error("❌ No account found with that email address.")
    st.stop()

# --- 5. PASSCODE LOCK SCREEN & FORGOT PIN ---
if not st.session_state.get("passcode_verified", False):
    conn = sqlite3.connect("muk_ai_secure.db")
    c = conn.cursor()
    c.execute("SELECT app_passcode, email FROM users WHERE username=?", (st.session_state.user_name,))
    row = c.fetchone()
    conn.close()
    correct_passcode = row[0] if row else ""
    user_email = row[1] if row else ""

    st.title(f"🔒 App Locked for {st.session_state.user_name}")
    st.markdown("### Enter your secure App Passcode / PIN to unlock your history and session:")
    
    with st.form("passcode_form"):
        entered_passcode = st.text_input("Enter Passcode / PIN", type="password", max_chars=6)
        unlock_btn = st.form_submit_button("Unlock App")
        if unlock_btn:
            if entered_passcode == correct_passcode:
                st.session_state.passcode_verified = True
                st.rerun()
            else:
                st.error("❌ Incorrect passcode. Try again.")
                
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        if st.button("❓ Forgot PIN? Send Reset Email"):
            if user_email:
                token = generate_reset_token(user_email, "pin")
                sent, info_msg = send_recovery_email(user_email, st.session_state.user_name, token, "pin")
                if sent:
                    st.success(info_msg)
                else:
                    st.error(info_msg)
            else:
                st.error("No email linked to this account.")
    with col_p2:
        if st.button("🚪 Log Out"):
            st.session_state.logged_in = False
            st.session_state.user_name = ""
            st.session_state.passcode_verified = False
            st.rerun()
    st.stop()

# --- 6. LOAD PERSISTENT HISTORY FOR THIS USER ---
if "global_history" not in st.session_state or not st.session_state.global_history:
    st.session_state.global_history = load_user_history(st.session_state.user_name)

# --- 7. API CLIENT & SETTINGS ---
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

st.sidebar.markdown(f"### 👤 Logged in as: `{st.session_state.user_name}`")
if st.sidebar.button("🔒 Lock App"):
    st.session_state.passcode_verified = False
    st.rerun()
if st.sidebar.button("🚪 Log Out"):
    st.session_state.logged_in = False
    st.session_state.user_name = ""
    st.session_state.passcode_verified = False
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("👤 User Avatar Style")
user_avatar_choice = st.sidebar.radio("Choose Avatar", ["👦 AI Boy", "👧 AI Girl"], index=0)
user_avatar_icon = "👨‍💻" if "Boy" in user_avatar_choice else "👩‍💻"
bot_avatar_icon = "🤖"

WORLD_LANGUAGES = [
    "English", "Հայերեն (Armenian)", "Русский (Russian)", "Español (Spanish)", 
    "Français (French)", "Deutsch (German)", "Chinese (Mandarin / 简体中文)", 
    "Arabic (العربية)", "Portuguese (Português)", "Japanese (日本語)", 
    "Hindi (हिन्दी)", "Korean (한국어)", "Italiano (Italian)", "Turkish (Türkçe)", 
    "Dutch (Nederlands)", "Greek (Ελληνικά)", "Polish (Polski)", "Persian (فارسی)", 
    "Hebrew (עברית)", "Swedish (Svenska)", "Ukrainian (Українська)", "Czech (Čeština)", 
    "Vietnamese (Tiếng Việt)", "Thai (ไทย)", "Indonesian (Bahasa Indonesia)", 
    "Bengali (বাংলা)", "Urdu (اردو)", "Swahili (Kiswahili)", "Custom / Other Language..."
]

st.sidebar.markdown("---")
st.sidebar.subheader("🌐 Global Language Settings")
sel_lang_sidebar = st.sidebar.selectbox("Choose AI Output Language", WORLD_LANGUAGES, index=0)

if sel_lang_sidebar == "Custom / Other Language...":
    custom_lang = st.sidebar.text_input("Enter Any World Language Name", placeholder="e.g., Georgian, Basque...")
    selected_language = custom_lang if custom_lang.strip() else "English"
else:
    selected_language = sel_lang_sidebar

st.sidebar.markdown("---")
st.sidebar.subheader("🔊 Audio Settings")
enable_natural_voice = st.sidebar.toggle("Enable Natural Voice 🔊", value=True)

st.sidebar.markdown("---")
st.sidebar.subheader("📜 Saved History")
if st.session_state.global_history:
    for idx, past_item in enumerate(reversed(st.session_state.global_history[-6:])):
        st.sidebar.caption(f"{idx+1}. {past_item}")
    if st.sidebar.button("Clear History"):
        clear_user_history_db(st.session_state.user_name)
        st.session_state.global_history = []
        st.rerun()
else:
    st.sidebar.write("No history saved yet.")

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

st.title(f"Hello, {st.session_state.user_name}!")
st.markdown("Your ultimate assistant with Aurora Borealis Gradients, Sound FX, and Holographic HUD!")

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11 = st.tabs([
    "📚 Homework", 
    "✍️ Essay", 
    "📊 Presentation", 
    "🎨 Visuals", 
    "💬 Muk Chat",
    "🧮 Calculator",
    "🧠 Exam Prep",
    "🔤 Translator",
    "📅 Study Planner",
    "🧪 Science & STEM",
    "✉️ Email Writer"
])

PRIMARY_MODEL = "gemini-3.8-flash"

def safe_generate(client_obj, contents):
    config = types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
    last_error = None
    for attempt in range(4):
        try:
            return client_obj.models.generate_content(
                model=PRIMARY_MODEL, 
                contents=contents,
                config=config
            )
        except Exception as e:
            last_error = e
            err_str = str(e).upper()
            if "503" in err_str or "UNAVAILABLE" in err_str or "429" in err_str:
                sleep_duration = 2 * (2 ** attempt)
                time.sleep(sleep_duration)
                continue
            break
    raise last_error

def safe_generate_stream(client_obj, contents):
    config = types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
    last_error = None
    for attempt in range(4):
        try:
            return client_obj.models.generate_content_stream(
                model=PRIMARY_MODEL, 
                contents=contents,
                config=config
            )
        except Exception as e:
            last_error = e
            err_str = str(e).upper()
            if "503" in err_str or "UNAVAILABLE" in err_str or "429" in err_str:
                sleep_duration = 2 * (2 ** attempt)
                time.sleep(sleep_duration)
                continue
            break
    raise last_error

def safe_generate_image(client_obj, prompt_text):
    config = types.GenerateContentConfig(
        response_modalities=["IMAGE", "TEXT"],
        system_instruction=SYSTEM_INSTRUCTION
    )
    last_error = None
    for attempt in range(4):
        try:
            return client_obj.models.generate_content(
                model=PRIMARY_MODEL,
                contents=f"Generate a high quality detailed image based on this description: {prompt_text}",
                config=config
            )
        except Exception as e:
            last_error = e
            err_str = str(e).upper()
            if "503" in err_str or "UNAVAILABLE" in err_str or "429" in err_str:
                sleep_duration = 2 * (2 ** attempt)
                time.sleep(sleep_duration)
                continue
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
                    
                    hist_entry = f"Homework: {query_text[:40]}..."
                    st.session_state.global_history.append(hist_entry)
                    save_user_history_item(st.session_state.user_name, hist_entry)
                    
                    st.success("Solution:")
                    st.write(solution_text)
                    speak_natural_voice(solution_text[:300])
                    st.download_button(label="📥 Download Solution as Text File", data=solution_text, file_name="muk_ai_homework_solution.txt", mime="text/plain", key="dl_hw")
                except Exception as e:
                    st.error(f"Error: {e}")

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
                    
                    hist_entry = f"Essay: {essay_topic[:40]}"
                    st.session_state.global_history.append(hist_entry)
                    save_user_history_item(st.session_state.user_name, hist_entry)
                    
                    st.success("Generated Text:")
                    st.write(essay_text)
                    speak_natural_voice("Your essay has been generated successfully!")
                    st.download_button(label="📥 Download Essay as Text File", data=essay_text, file_name="muk_ai_essay.txt", mime="text/plain", key="dl_essay")
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Please enter a topic.")

with tab3:
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
                    
                    hist_entry = f"Presentation: {pres_topic[:40]}"
                    st.session_state.global_history.append(hist_entry)
                    save_user_history_item(st.session_state.user_name, hist_entry)
                    
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

with tab4:
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
                                        
                                        hist_entry = f"Visual: {img_prompt[:40]}"
                                        st.session_state.global_history.append(hist_entry)
                                        save_user_history_item(st.session_state.user_name, hist_entry)
                                        
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

with tab5:
    st.header("💬 Muk AI Chat")
    st.write("Chat freely with your personal AI assistant.")
    
    chat_mode = st.selectbox(
        "Gemini Auto",
        ["General Chat", "Homework", "Essay", "Calculator", "Science & STEM", "Email Writer"],
        key="chat_mode_dropdown"
    )
    
    web_search_toggle = st.toggle("🌐 Enable Web Research Mode", value=False)
    
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
        
    for message in st.session_state.chat_messages:
        curr_avatar = user_avatar_icon if message["role"] == "user" else bot_avatar_icon
        with st.chat_message(message["role"], avatar=curr_avatar):
            st.markdown(message["content"])
            
    if chat_input := st.chat_input(f"Ask Muk AI ({chat_mode} Mode)..."):
        actual_input = chat_input
        if chat_mode != "General Chat":
            actual_input = f"[{chat_mode} Mode Request]: {chat_input}"
            
        st.session_state.chat_messages.append({"role": "user", "content": actual_input})
        with st.chat_message("user", avatar=user_avatar_icon):
            st.markdown(actual_input)
            
        if client:
            with st.chat_message("assistant", avatar=bot_avatar_icon):
                try:
                    history_payload = []
                    if web_search_toggle:
                        history_payload.append("System Notice: Provide up-to-date, comprehensive, well-researched web answers with citations where appropriate.")
                    
                    for m in st.session_state.chat_messages[-6:]:
                        history_payload.append(f"{m['role'].capitalize()}: {m['content']}")
                        
                    response_stream = safe_generate_stream(client, history_payload)
                    
                    def stream_generator():
                        for chunk in response_stream:
                            if chunk.text:
                                yield chunk.text
                                
                    reply = st.write_stream(stream_generator())
                    st.session_state.chat_messages.append({"role": "assistant", "content": reply})
                    
                    hist_entry = f"Chat ({chat_mode}): {chat_input[:30]}..."
                    st.session_state.global_history.append(hist_entry)
                    save_user_history_item(st.session_state.user_name, hist_entry)
                    
                    speak_natural_voice(reply[:200])
                except Exception as e:
                    st.error(f"Error: {e}")

with tab6:
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
                    
                    hist_entry = f"Calculator: {calc_input[:30]}"
                    st.session_state.global_history.append(hist_entry)
                    save_user_history_item(st.session_state.user_name, hist_entry)
                    
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
                hist_entry = f"Graph: {calc_input[:30]}"
                st.session_state.global_history.append(hist_entry)
                save_user_history_item(st.session_state.user_name, hist_entry)
            except Exception as e:
                st.error(f"Could not plot expression: {e}. Try entering a formula with 'x', e.g., 'x**2' or 'sin(x)'.")

with tab7:
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
                    
                    hist_entry = f"Exam Prep: {study_topic[:30]}"
                    st.session_state.global_history.append(hist_entry)
                    save_user_history_item(st.session_state.user_name, hist_entry)
                    
                    st.success("Study Material Ready:")
                    st.write(response.text)
                    speak_natural_voice("Your exam practice materials are ready!")
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Please enter a topic or paste study notes.")

with tab8:
    st.header("🔤 Universal Multilingual Translator")
    st.write("Translate text into any language in the world while preserving context, idioms, and natural tone.")
    
    trans_text = st.text_input("Enter text to translate", placeholder="e.g., How are you doing today?", key="trans_box")
    
    trans_src_options = ["Auto-Detect"] + WORLD_LANGUAGES
    trans_target_options = WORLD_LANGUAGES
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        src_lang_sel = st.selectbox("From Language", trans_src_options, index=0, key="src_lang")
        if src_lang_sel == "Custom / Other Language...":
            src_lang_final = st.text_input("Specify From Language", placeholder="e.g., Latin, Georgian...", key="src_lang_custom")
        else:
            src_lang_final = src_lang_sel
            
    with col_t2:
        target_lang_sel = st.selectbox("To Language", trans_target_options, index=1, key="target_lang")
        if target_lang_sel == "Custom / Other Language...":
            target_lang_final = st.text_input("Specify To Language", placeholder="e.g., Basque, Kurdish...", key="target_lang_custom")
        else:
            target_lang_final = target_lang_sel
        
    if st.button("Translate with Context"):
        if not client:
            st.error("API client not initialized.")
        elif trans_text:
            with st.spinner("Translating..."):
                try:
                    prompt = f"Translate the following text from {src_lang_final} to {target_lang_final}. Preserve exact natural context and explain any idioms or cultural nuances if present: {trans_text}"
                    response = safe_generate(client, prompt)
                    
                    hist_entry = f"Translation: {trans_text[:30]}"
                    st.session_state.global_history.append(hist_entry)
                    save_user_history_item(st.session_state.user_name, hist_entry)
                    
                    st.success("Translation:")
                    st.write(response.text)
                    speak_natural_voice(response.text[:300])
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Please enter text to translate.")

with tab9:
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
                    
                    hist_entry = f"Planner: {subjects[:30]}"
                    st.session_state.global_history.append(hist_entry)
                    save_user_history_item(st.session_state.user_name, hist_entry)
                    
                    st.success("Your Personalized Timetable:")
                    st.write(response.text)
                    speak_natural_voice("Your study schedule is ready!")
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Please enter your subjects or topics.")

with tab10:
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
                    
                    hist_entry = f"STEM: {stem_concept[:30]}"
                    st.session_state.global_history.append(hist_entry)
                    save_user_history_item(st.session_state.user_name, hist_entry)
                    
                    st.success("Scientific Breakdown:")
                    st.write(response.text)
                    speak_natural_voice("Scientific explanation complete!")
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Please enter a science question or formula.")

with tab11:
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
                    
                    hist_entry = f"Email: {email_purpose[:30]}"
                    st.session_state.global_history.append(hist_entry)
                    save_user_history_item(st.session_state.user_name, hist_entry)
                    
                    st.success("Drafted Email:")
                    st.write(response.text)
                    speak_natural_voice("Your email draft is ready!")
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Please enter the main purpose of your email.")

st.sidebar.markdown("---")
st.sidebar.markdown("<p style='font-size: 12px; color: #f8fafc; text-align: center;'>My AI created by Simonyan Mikayel from Armenia</p>", unsafe_allow_html=True)
