import json
import speech_recognition as sr
import PyPDF2
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os

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
    # chat_id -> {title, messages}
    st.session_state.chats = {}

if "active_chat" not in st.session_state:
    st.session_state.active_chat = None

if "theme" not in st.session_state:
    st.session_state.theme = "light"


# =========================
# CREATE NEW CHAT
# =========================
def create_new_chat():
    chat_id = f"chat_{len(st.session_state.chats) + 1}"

    st.session_state.chats[chat_id] = {
        "title": "New Chat",
        "messages": [
            {"role": "system", "content": "You are a helpful AI assistant."}
        ]
    }

    st.session_state.active_chat = chat_id


# initialize first chat
if not st.session_state.chats:
    create_new_chat()


# =========================
# AUTO TITLE GENERATOR
# =========================
def generate_title(text):
    return text[:30] + "..." if len(text) > 30 else text


# =========================
# SIDEBAR
# =========================
with st.sidebar:

    st.header("💬 Chats")

    if st.button("➕ New Chat"):
        create_new_chat()
        st.rerun()

    st.markdown("---")

    # SHOW CHAT TITLES (NOT Chat 1, Chat 2)
    for chat_id, chat_data in st.session_state.chats.items():
        if st.button(chat_data["title"]):
            st.session_state.active_chat = chat_id
            st.rerun()

    st.markdown("---")

    st.header("⚙️ Tools")

    st.session_state.theme = st.radio("Theme", ["Light", "Dark"]).lower()

    if st.button("🗑 Clear Chat"):
        st.session_state.chats[st.session_state.active_chat]["messages"] = [
            {"role": "system", "content": "You are a helpful AI assistant."}
        ]
        st.rerun()

    st.markdown("---")

    # VOICE INPUT
    st.subheader("🎤 Voice Input")

    if st.button("Start Speaking"):
        recognizer = sr.Recognizer()

        with sr.Microphone() as source:
            st.info("Listening...")
            audio = recognizer.listen(source)

        try:
            text = recognizer.recognize_google(audio)
            st.success(text)

            chat = st.session_state.chats[st.session_state.active_chat]["messages"]

            chat.append({"role": "user", "content": text})

        except:
            st.error("Could not recognize speech")

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
# TITLE
# =========================
st.title("🤖 AI Chatbot")


# =========================
# GET ACTIVE CHAT
# =========================
chat = st.session_state.chats[st.session_state.active_chat]["messages"]


# =========================
# CHAT DISPLAY
# =========================
st.markdown('<div class="chat-box">', unsafe_allow_html=True)

for msg in chat:
    if msg["role"] == "system":
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
    chat.append({"role": "user", "content": prompt})

    # AUTO TITLE UPDATE (ONLY FIRST USER MESSAGE)
    if st.session_state.chats[st.session_state.active_chat]["title"] == "New Chat":
        st.session_state.chats[st.session_state.active_chat]["title"] = generate_title(prompt)

    st.rerun()


# =========================
# AI RESPONSE
# =========================
if chat[-1]["role"] == "user":

    typing_placeholder = st.empty()
    typing_placeholder.markdown("🤖 **AI is typing...**")

    try:
        response = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=chat
        )

        reply = response.choices[0].message.content

        typing_placeholder.empty()

        chat.append({"role": "assistant", "content": reply})

        st.rerun()

    except Exception as e:
        typing_placeholder.empty()
        st.error(e)
