import json
import os
import speech_recognition as sr
import PyPDF2
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

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
# SAFE INIT (PREVENT OLD ERRORS)
# =========================
if "initialized" not in st.session_state:
    st.session_state.clear()
    st.session_state["initialized"] = True


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
# CREATE NEW CHAT (FIXED STRUCTURE)
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


if not st.session_state.chats:
    create_new_chat()


# =========================
# GENERATE TITLE
# =========================
def generate_title(text):
    return text[:35] + "..." if len(text) > 35 else text


# =========================
# GET SAFE CHAT
# =========================
def get_chat():
    chat_id = st.session_state.active_chat

    if chat_id is None or chat_id not in st.session_state.chats:
        create_new_chat()
        chat_id = st.session_state.active_chat

    chat_data = st.session_state.chats[chat_id]

    if "messages" not in chat_data or not isinstance(chat_data["messages"], list):
        chat_data["messages"] = [
            {"role": "system", "content": "You are a helpful AI assistant."}
        ]

    return chat_data


chat_data = get_chat()
messages = chat_data["messages"]


# =========================
# SIDEBAR
# =========================
with st.sidebar:

    st.header("💬 Chats")

    if st.button("➕ New Chat"):
        create_new_chat()
        st.rerun()

    st.markdown("---")

    for chat_id, data in st.session_state.chats.items():
        title = data.get("title", "Untitled Chat")

        if st.button(title):
            st.session_state.active_chat = chat_id
            st.rerun()

    st.markdown("---")

    st.header("⚙️ Tools")

    st.session_state.theme = st.radio("Theme", ["Light", "Dark"]).lower()

    if st.button("🗑 Clear Chat"):
        chat_data["messages"] = [
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
            messages.append({"role": "user", "content": text})

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
            t = page.extract_text()
            if t:
                pdf_text += t

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
# CHAT DISPLAY (100% SAFE)
# =========================
st.markdown('<div class="chat-box">', unsafe_allow_html=True)

for msg in messages:

    if not isinstance(msg, dict):
        continue

    role = msg.get("role", "")
    content = msg.get("content", "")

    if role == "system":
        continue

    if role == "user":
        st.markdown(f"<div class='user-msg'>🧑 {content}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='bot-msg'>🤖 {content}</div>", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)


# =========================
# CHAT INPUT
# =========================
prompt = st.chat_input("Message ChatGPT...")

if prompt:
    messages.append({"role": "user", "content": prompt})

    if chat_data["title"] == "New Chat":
        chat_data["title"] = generate_title(prompt)

    st.rerun()


# =========================
# AI RESPONSE
# =========================
if messages and messages[-1].get("role") == "user":

    placeholder = st.empty()
    placeholder.markdown("🤖 **AI is typing...**")

    try:
        response = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=messages
        )

        reply = response.choices[0].message.content

        placeholder.empty()

        messages.append({"role": "assistant", "content": reply})

        st.rerun()

    except Exception as e:
        placeholder.empty()
        st.error(e)
