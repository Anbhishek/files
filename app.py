"""AnythingGPT - a private, local Streamlit assistant powered by Ollama."""

from __future__ import annotations

import re

import streamlit as st

from auth import (
    change_password,
    create_user,
    get_user,
    login_user,
    request_password_reset,
    reset_password,
    update_profile,
)
from background import add_starfield_background
from llm_backend import ask_llm_stream
from rag import clear_documents, retrieve_context
from storage import (
    create_conversation,
    delete_conversation,
    get_conversation,
    list_conversations,
    save_conversation,
)


st.set_page_config(
    page_title="AnythingGPT",
    page_icon="✦",
    layout="wide",
    # "auto" collapses the sidebar automatically on narrow / mobile screens
    # and keeps it open on desktop.
    initial_sidebar_state="auto",
)

# ---------------------------------------------------------------------------
# Styling. Streamlit doesn't let us build one true merged "pill" input like
# Claude's DOM does, but giving matching widgets a `key` gives each of them a
# `st-key-<key>` class we can target precisely, which gets us very close.
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
h1, h2, h3, h4, h5, h6, p, span, label, button, div, input {
    color: #ffffff !important;
    fill: #ffffff !important;
}
input::placeholder { color: rgba(255, 255, 255, 0.5) !important; }
html, body { background-color: #0a0e27 !important; color: #ffffff !important; }
[data-testid="stAppViewContainer"] { background-color: transparent !important; }
[data-testid="stMainBlockContainer"] { background-color: transparent !important; padding: 0 !important; }
[data-testid="stForm"], [data-testid="stTextInput"], [data-testid="stRadio"],
[data-testid="stMarkdownContainer"] { background-color: transparent !important; }
.stTabs { background-color: transparent !important; }
[role="tab"] { color: #a0aec0 !important; background-color: transparent !important; border: none !important; }
[role="tab"][aria-selected="true"] { color: #667eea !important; border-bottom: 2px solid #667eea !important; }
input {
    background-color: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    border-radius: 0.5rem !important;
    color: #ffffff !important;
    padding: 0.75rem !important;
}
button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 0.5rem !important;
    padding: 0.6rem 1.1rem !important;
    font-weight: 600 !important;
    transition: transform 0.12s ease, opacity 0.12s ease;
}
button:hover { opacity: 0.92; }
[data-testid="stAlert"] { background-color: transparent !important; color: #ffffff !important; }

/* ---------------- Sidebar: small, fixed width, own scrollbar ---------------- */
[data-testid="stSidebar"] {
    width: 260px !important;
    min-width: 260px !important;
    max-width: 260px !important;
    background-color: #0d1224 !important;
    border-right: 1px solid rgba(255,255,255,0.08);
}
[data-testid="stSidebarUserContent"] {
    max-height: 100vh;
    overflow-y: auto !important;
}
[data-testid="stSidebar"] button {
    background: transparent !important;
    text-align: left !important;
    justify-content: flex-start !important;
    font-weight: 400 !important;
    padding: 0.45rem 0.6rem !important;
    box-shadow: none !important;
    border-radius: 0.5rem !important;
}
[data-testid="stSidebar"] button:hover { background: rgba(255,255,255,0.07) !important; }
.st-key-new_chat_btn button {
    background: rgba(102,126,234,0.18) !important;
    font-weight: 600 !important;
    border: 1px solid rgba(102,126,234,0.4) !important;
}

/* ---------------- Scrollable message pane ---------------- */
.st-key-chat_scroll {
    max-width: 840px;
    margin: 0 auto;
    padding: 0.5rem 0.35rem 1rem;
    height: calc(100vh - 235px) !important;
    overflow-y: auto !important;
}

/* Claude-style bubbles: user on the right, assistant on the left */
[data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"] { display: none !important; }
[data-testid="stChatMessage"] { background: transparent !important; padding: 0.15rem 0 !important; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) { flex-direction: row-reverse; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 1.1rem 1.1rem 0.25rem 1.1rem;
    margin-left: auto;
    max-width: 75%;
    padding: 0.65rem 1rem !important;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) [data-testid="stChatMessageContent"] {
    background: rgba(255,255,255,0.045);
    border-radius: 1.1rem 1.1rem 1.1rem 0.25rem;
    max-width: 88%;
    padding: 0.65rem 1rem !important;
}
[data-testid="stChatMessage"] .stButton button {
    background: transparent !important;
    color: #a0aec0 !important;
    font-size: 0.78rem !important;
    padding: 0.15rem 0.4rem !important;
}

/* ---------------- Composer pill: text · mic · send ---------------- */
.st-key-composer_wrap {
    max-width: 840px;
    margin: 0.4rem auto 0.75rem;
    padding: 0.3rem 0.4rem 0.3rem 1.1rem;
    border: 1px solid rgba(255,255,255,0.14);
    border-radius: 999px;
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(12px);
    position: sticky;
    bottom: 0.6rem;
    z-index: 20;
}
.st-key-composer_wrap input {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0.55rem 0.25rem !important;
}
.st-key-composer_wrap [data-testid="stHorizontalBlock"] { align-items: center !important; }
.st-key-mic_toggle_btn button, .st-key-send_btn button {
    border-radius: 999px !important;
    width: 2.35rem !important;
    height: 2.35rem !important;
    min-width: 2.35rem !important;
    padding: 0 !important;
    font-size: 1.05rem !important;
    line-height: 1 !important;
}
.st-key-mic_toggle_btn button { background: rgba(255,255,255,0.08) !important; }
.st-key-mic_toggle_btn.mic-active button { background: linear-gradient(135deg,#667eea,#764ba2) !important; }
.st-key-send_btn button { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important; }
.st-key-mic_toggle_btn button:hover, .st-key-send_btn button:hover { transform: scale(1.08); }

.st-key-recorder_card {
    max-width: 500px;
    margin: 0 auto 0.75rem;
    padding: 0.8rem 1rem;
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 1rem;
    background: rgba(255,255,255,0.04);
}

/* ---------------- Mobile ---------------- */
@media (max-width: 640px) {
    .st-key-chat_scroll { height: calc(100vh - 205px) !important; padding: 0.35rem 0.15rem 0.75rem; }
    .st-key-composer_wrap { max-width: 96%; padding: 0.25rem 0.3rem 0.25rem 0.9rem; }
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"],
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) [data-testid="stChatMessageContent"] {
        max-width: 92%;
    }
}
</style>
""",
    unsafe_allow_html=True,
)


def init_state() -> None:
    defaults = {
        "authenticated": False,
        "user": None,
        "conversation_id": None,
        "messages": [],
        "documents": [],
        "auth_mode": None,
        "reset_username": None,
        "composer_key": 0,
        "show_recorder": False,
        "pending_prompt": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def clean_title(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return (text[:42] + "…") if len(text) > 43 else (text or "New conversation")


def speak(text: str) -> None:
    import json

    safe_text = json.dumps(re.sub(r"<[^>]+>", "", text))
    st.components.v1.html(
        f"""<script>
        const utterance = new SpeechSynthesisUtterance({safe_text});
        utterance.rate = 1; utterance.pitch = 1;
        window.parent.speechSynthesis.cancel(); window.parent.speechSynthesis.speak(utterance);
        </script>""",
        height=0,
    )


def auth_screen() -> None:
    add_starfield_background()

    st.markdown(
        "<div style='text-align:center; padding:2rem 0 1rem; font-size:2rem; font-weight:700;'>✦</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div style='text-align:center; font-size:2rem; font-weight:700; margin-bottom:0.25rem;'>AnythingGPT</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div style='text-align:center; color:#a0aec0; margin-bottom:2rem;'>Your private AI workspace</div>",
        unsafe_allow_html=True,
    )

    auth_tab, signup_tab, reset_tab = st.tabs(
        ["Sign in", "Create account", "Forgot password"]
    )

    with auth_tab:
        username = st.text_input(
            "Username", placeholder="Enter your username", label_visibility="collapsed"
        )
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            label_visibility="collapsed",
        )
        if st.button("Sign in", use_container_width=True):
            if username and password:
                user = login_user(username, password)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("❌ Incorrect username or password")
            else:
                st.warning("Please enter username and password")

    with signup_tab:
        name = st.text_input(
            "Your name", placeholder="Ada Lovelace", label_visibility="collapsed"
        )
        signup_user = st.text_input(
            "Choose a username", placeholder="ada", label_visibility="collapsed"
        )
        signup_pass = st.text_input(
            "Choose a password",
            type="password",
            placeholder="Min. 6 characters",
            label_visibility="collapsed",
        )
        signup_email = st.text_input(
            "Email (optional)",
            placeholder="ada@example.com",
            label_visibility="collapsed",
        )
        signup_phone = st.text_input(
            "Phone (optional)",
            placeholder="+1 555 123 4567",
            label_visibility="collapsed",
        )
        if st.button("Create local account", use_container_width=True):
            if name and signup_user and signup_pass:
                ok, message = create_user(
                    name, signup_user, signup_pass, signup_email, signup_phone
                )
                if ok:
                    st.session_state.auth_mode = None
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
            else:
                st.warning("Please fill in name, username, and password")

    with reset_tab:
        st.caption("Request a one-time code, then use it below to set a new password.")
        reset_user = st.text_input(
            "Username",
            placeholder="Enter your username",
            key="reset_user_input",
            label_visibility="collapsed",
        )
        channel = st.radio("Send code via", ["email", "phone"], horizontal=True)
        if st.button("Send reset code", use_container_width=True):
            if reset_user:
                ok, message = request_password_reset(reset_user, channel)
                if ok:
                    st.session_state.reset_username = reset_user
                else:
                    st.error(f"❌ {message}")
            else:
                st.warning("Please enter username")

        if st.session_state.get("reset_username"):
            st.divider()
            reset_code = st.text_input(
                "6-digit code", placeholder="000000", label_visibility="collapsed"
            )
            new_pass = st.text_input(
                "New password",
                type="password",
                placeholder="Min. 6 characters",
                label_visibility="collapsed",
            )
            if st.button("Set new password", use_container_width=True):
                if reset_code and new_pass:
                    ok, message = reset_password(
                        st.session_state.reset_username, reset_code, new_pass
                    )
                    if ok:
                        st.session_state.auth_mode = None
                        st.session_state.reset_username = None
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.warning("Please fill in code and new password")


def select_conversation(conversation_id: str) -> None:
    conversation = get_conversation(st.session_state.user["username"], conversation_id)
    if conversation:
        st.session_state.conversation_id = conversation_id
        st.session_state.messages = conversation["messages"]


def new_chat() -> None:
    st.session_state.conversation_id = None
    st.session_state.messages = []
    st.session_state.documents = []
    clear_documents()


def save_current_chat() -> None:
    if not st.session_state.messages:
        return
    if st.session_state.conversation_id is None:
        st.session_state.conversation_id = create_conversation(
            st.session_state.user["username"],
            clean_title(st.session_state.messages[0]["content"]),
            st.session_state.messages,
        )
    else:
        save_conversation(
            st.session_state.user["username"],
            st.session_state.conversation_id,
            st.session_state.messages,
        )


def account_settings_panel() -> None:
    user = st.session_state.user
    full = get_user(user["username"]) or {}
    with st.expander("⚙️ Account"):
        st.caption(f"Signed in as **{user['display_name']}**  ·  @{user['username']}")

        st.markdown("**Contact details**")
        new_email = st.text_input(
            "Email", value=full.get("email", ""), key="acct_email"
        )
        new_phone = st.text_input(
            "Phone", value=full.get("phone", ""), key="acct_phone"
        )
        if st.button(
            "Save contact info", key="acct_save_btn", use_container_width=True
        ):
            ok, message = update_profile(
                user["username"], email=new_email, phone=new_phone
            )
            st.success(message) if ok else st.error(f"❌ {message}")

        st.divider()
        st.markdown("**Change password**")
        cur_pw = st.text_input("Current password", type="password", key="acct_cur_pw")
        new_pw = st.text_input("New password", type="password", key="acct_new_pw")
        if st.button("Update password", key="acct_pw_btn", use_container_width=True):
            if cur_pw and new_pw:
                ok, message = change_password(user["username"], cur_pw, new_pw)
                st.success(message) if ok else st.error(f"❌ {message}")
            else:
                st.warning("Fill in both password fields")

        st.divider()
        if st.button("Log out", key="logout_btn", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.conversation_id = None
            st.session_state.messages = []
            st.rerun()


def sidebar() -> None:
    with st.sidebar:
        st.markdown(
            "<div style='font-weight:700;font-size:1.1rem;padding:0.25rem 0 1rem;'>✦ AnythingGPT</div>",
            unsafe_allow_html=True,
        )
        if st.button("＋  New chat", use_container_width=True, key="new_chat_btn"):
            new_chat()
            st.rerun()

        st.markdown(
            "<div style='color:#a0aec0;font-size:0.72rem;letter-spacing:0.04em;margin:1rem 0 0.25rem;'>RECENT</div>",
            unsafe_allow_html=True,
        )

        conversations = list_conversations(st.session_state.user["username"])
        if not conversations:
            st.caption("No conversations yet")
        for chat in conversations:
            col_title, col_delete = st.columns([0.82, 0.18])
            is_active = chat["id"] == st.session_state.conversation_id
            label = ("● " if is_active else "") + chat["title"]
            if col_title.button(
                label, key=f"chat_{chat['id']}", use_container_width=True
            ):
                select_conversation(chat["id"])
                st.rerun()
            if col_delete.button(
                "🗑", key=f"del_{chat['id']}", use_container_width=True
            ):
                delete_conversation(st.session_state.user["username"], chat["id"])
                if is_active:
                    new_chat()
                st.rerun()

        st.markdown("<div style='margin-top:1.25rem;'></div>", unsafe_allow_html=True)
        account_settings_panel()


def handle_user_message(prompt: str) -> None:
    """Append the user's message, stream the assistant's reply, and persist the chat."""
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    context, sources = retrieve_context(prompt)
    with st.chat_message("assistant"):
        response = st.write_stream(ask_llm_stream(st.session_state.messages, context))
        if sources:
            extra = "\n\n---\n📚 **PDF sources:** " + ", ".join(sorted(set(sources)))
            st.markdown(extra)
            response += extra

    st.session_state.messages.append({"role": "assistant", "content": response})
    save_current_chat()
    st.rerun()


def _composer_key() -> str:
    return f"chat_box_{st.session_state.composer_key}"


def _submit_current_message() -> None:
    """Callback: fires only when the composer's own text input submits (Enter / blur)."""
    key = _composer_key()
    text = st.session_state.get(key, "").strip()
    if text:
        st.session_state.pending_prompt = text
        st.session_state.composer_key += (
            1  # rotate widget key so the box clears next render
        )


def main_chat() -> None:
    add_starfield_background()
    sidebar()

    st.markdown(
        "<div style='text-align:center; max-width:840px; margin:0 auto; "
        "padding:0.75rem 0 0.25rem; font-size:1.4rem; font-weight:700;'>AnythingGPT</div>",
        unsafe_allow_html=True,
    )

    with st.container(key="chat_scroll"):
        if not st.session_state.messages:
            st.markdown(
                "<div style='text-align:center; padding:3rem 0 1rem; font-size:1.7rem; font-weight:700;'>"
                "What can I help with?</div>",
                unsafe_allow_html=True,
            )
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message["role"] == "assistant":
                    if st.button("🔊 Listen", key="speak_" + str(id(message))):
                        speak(message["content"])

    # ---- Composer: text · mic · send, styled as one pill ----
    with st.container(key="composer_wrap"):
        col_text, col_mic, col_send = st.columns([0.80, 0.10, 0.10])
        with col_text:
            st.text_input(
                "",
                key=_composer_key(),
                label_visibility="collapsed",
                placeholder="Ask AnythingGPT…",
                on_change=_submit_current_message,
            )
        with col_mic:
            mic_clicked = st.button(
                "🎤", key="mic_toggle_btn", use_container_width=True
            )
        with col_send:
            send_clicked = st.button("↑", key="send_btn", use_container_width=True)

    if mic_clicked:
        st.session_state.show_recorder = not st.session_state.show_recorder
    if send_clicked:
        _submit_current_message()

    if st.session_state.show_recorder:
        with st.container(key="recorder_card"):
            st.caption("🎤 Record a voice message, then send it as your prompt")
            audio = st.audio_input("", label_visibility="collapsed", key="voice_audio")
            if st.button(
                "Transcribe & send", use_container_width=True, key="transcribe_btn"
            ):
                if audio:
                    from voice import transcribe_audio

                    with st.spinner("Transcribing locally…"):
                        text, error = transcribe_audio(audio)
                    if error:
                        st.error(error)
                    elif text.strip():
                        st.session_state.show_recorder = False
                        st.session_state.pending_prompt = text.strip()
                    else:
                        st.info("Didn't catch any speech, try again")
                else:
                    st.info("Record or upload audio first")

    if st.session_state.pending_prompt:
        prompt = st.session_state.pending_prompt
        st.session_state.pending_prompt = None
        handle_user_message(prompt)


init_state()
auth_screen() if not st.session_state.authenticated else main_chat()
