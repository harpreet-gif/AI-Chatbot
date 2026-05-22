import json
import speech_recognition as sr
import PyPDF2
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os

if "INIT_DONE" not in st.session_state:
    st.session_state.clear()
    st.session_state["INIT_DONE"] = True

# =========================
# LOAD ENV
# =========================
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="AI Chatbot",
    page_icon="🤖",
    layout="wide"
)

# =========================
# SESSION STATE
# =========================
if "chats" not in st.session_state:
    st.session_state.chats = {}

if "active_chat" not in st.session_state:
    st.session_state.active_chat = None

if "theme" not in st.session_state:
    st.session_state.theme = "light"


# =========================
# CREATE NEW CHAT
# =========================
def create_new_chat():
    chat_id = f"Chat {len(st.session_state.chats) + 1}"
    st.session_state.chats[chat_id] = [
        {"role": "system", "content": "You are a helpful AI assistant."}
    ]
    st.session_state.active_chat = chat_id


if not st.session_state.chats:
    create_new_chat()

# =========================
# SIDEBAR
# =========================
with st.sidebar:

    st.header("💬 Chats")

    if st.button("➕ New Chat"):
        create_new_chat()
        st.rerun()

    st.markdown("---")

    for chat_name in st.session_state.chats.keys():
        if st.button(chat_name):
            st.session_state.active_chat = chat_name
            st.rerun()

    st.markdown("---")

    st.header("⚙️ Tools")

    st.session_state.theme = st.radio("Theme", ["Light", "Dark"]).lower()

    if st.button("🗑 Clear Chat"):
        st.session_state.chats[st.session_state.active_chat] = [
            {"role": "system", "content": "You are a helpful AI assistant."}
        ]
        st.rerun()

    st.markdown("---")

    # VOICE INPUT
    st.subheader("🎤 Voice Input")

    if st.button("Start Speaking"):

try:
        recognizer = sr.Recognizer()

        with sr.Microphone() as source:
            st.info("Listening...")
            audio = recognizer.listen(source)

        text = recognizer.recognize_google(audio)
        st.success(text)

        st.session_state.chats[st.session_state.active_chat].append(
            {"role": "user", "content": text}
        )

    except Exception:
        st.warning("🎤 Voice input works only in local system (not on Streamlit Cloud).")

    st.markdown("---")

    # PDF UPLOAD
    st.subheader("📄 PDF Upload")

    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

    pdf_text = ""

    if uploaded_file:
        reader = PyPDF2.PdfReader(uploaded_file)

        for page in reader.pages:
            text = page.extract_text()
            if text:
                pdf_text += text

        st.success("PDF Loaded!")

        if st.button("Summarize PDF"):
            try:
                response = client.chat.completions.create(
                    model="openai/gpt-3.5-turbo",
                    messages=[
                        {"role": "user", "content": f"Summarize this PDF:\n\n{pdf_text}"}
                    ]
                )

                st.write(response.choices[0].message.content)

            except Exception as e:
                st.error(e)

    st.markdown("---")
    st.caption("Made by Harpreet ✨")


# =========================
# CSS (PREMIUM UI + THEMES)
# =========================
st.markdown(f"""
<style>

/* MAIN BACKGROUND */
.main {{
    background-color: {'#0f172a' if st.session_state.theme == 'dark' else '#ffffff'};
}}

/* CHAT CONTAINER */
.chat-box {{
    max-width: 800px;
    margin: auto;
    padding-bottom: 120px;
}}

/* USER BUBBLE (GRADIENT PREMIUM) */
.user-msg {{
    background: linear-gradient(135deg, #60a5fa, #3b82f6, #2563eb);
    color: white;
    padding: 12px 16px;
    border-radius: 18px;
    margin: 10px 0;
    text-align: right;

    box-shadow: 0 8px 20px rgba(37, 99, 235, 0.35);
    border: 1px solid rgba(255,255,255,0.2);

    max-width: 75%;
    float: right;
    clear: both;
}}

/* BOT BUBBLE (GLASS STYLE LIGHT) */
.bot-msg {{
    background: linear-gradient(135deg, #f8fafc, #e2e8f0);
    color: #0f172a;
    padding: 12px 16px;
    border-radius: 18px;
    margin: 10px 0;
    text-align: left;

    box-shadow: 0 8px 18px rgba(0,0,0,0.08);
    border: 1px solid rgba(148,163,184,0.3);

    max-width: 75%;
    float: left;
    clear: both;
}}

/* DARK MODE OVERRIDES */
{"""
.user-msg {
    background: linear-gradient(135deg, #1d4ed8, #1e3a8a);
    color: white;
}

.bot-msg {
    background: linear-gradient(135deg, #1e293b, #0f172a);
    color: #e2e8f0;
    border: 1px solid #334155;
}
""" if st.session_state.theme == "dark" else ""}

/* SIDEBAR */
section[data-testid="stSidebar"] {{
    background-color: {'#111827' if st.session_state.theme == 'dark' else '#f8fafc'} !important;
}}

section[data-testid="stSidebar"] * {{
    color: {'#ffffff' if st.session_state.theme == 'dark' else '#0f172a'} !important;
}}

section[data-testid="stSidebar"] button {{
    background-color: {'#1f2937' if st.session_state.theme == 'dark' else '#e2e8f0'} !important;
    color: {'#ffffff' if st.session_state.theme == 'dark' else '#0f172a'} !important;
}}

.chat-box::after {{
    content: "";
    display: block;
    clear: both;
}}

</style>
""", unsafe_allow_html=True)


# =========================
# TITLE
# =========================
st.title("🤖 AI Chatbot")


# =========================
# CHAT DISPLAY
# =========================
st.markdown('<div class="chat-box">', unsafe_allow_html=True)

for msg in st.session_state.chats[st.session_state.active_chat]:
    if not isinstance(msg, dict) or msg.get("role") == "system":
        continue

    if msg["role"] == "user":
        st.markdown(f"<div class='user-msg'>🧑 {msg['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='bot-msg'>🤖 {msg['content']}</div>", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)


# =========================
# CHAT INPUT
# =========================
prompt = st.chat_input("Message ChatGPT...")

if prompt:
    st.session_state.chats[st.session_state.active_chat].append(
        {"role": "user", "content": prompt}
    )
    st.rerun()


# =========================
# AI RESPONSE (TYPING INDICATOR)
# =========================
if st.session_state.chats[st.session_state.active_chat][-1]["role"] == "user":

    typing_placeholder = st.empty()
    typing_placeholder.markdown("🤖 **AI is typing...**")

    try:
        response = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=st.session_state.chats[st.session_state.active_chat]
        )

        reply = response.choices[0].message.content

        typing_placeholder.empty()

        st.session_state.chats[st.session_state.active_chat].append(
            {"role": "assistant", "content": reply}
        )

        st.rerun()

    except Exception as e:
        typing_placeholder.empty()
        st.error(e)
