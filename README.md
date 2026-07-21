# SYRAX 
 **An AI private assistant**

A private, self-hosted AI chat assistant that runs entirely on your own machine. No API keys, no cloud LLM calls, no data leaving your computer — the model, your conversations, and your uploaded documents all stay local.

Built with [Streamlit](https://streamlit.io) for the interface and [Ollama](https://ollama.com) for local LLM inference, AnythingGPT gives you a Claude-style chat experience — streaming replies, conversation history, voice input, and document-aware answers — without sending anything to a third-party API.

---

## Why this exists (the theory)

Most AI chat apps are thin wrappers around a hosted API: your prompts, your files, and your conversation history all pass through someone else's servers. Syrax takes the opposite approach — the LLM itself (via Ollama) runs as a local process on your machine, and every other piece of the app (auth, storage, retrieval, voice) is built to match that same local-first principle:

- **Local inference, not a hosted API.** `llm_backend.py` talks to Ollama over its Python client (or CLI fallback) rather than an external HTTP API. The model, its weights, and the compute all live on your hardware.
- **Local accounts, not a cloud identity provider.** `auth.py` implements its own username/password system with salted PBKDF2 hashing (310,000 iterations) and file-based storage — no third-party auth service is involved.
- **Local storage, not a database service.** Conversations (`storage.py`) and accounts (`auth.py`) are persisted as JSON files under `data/`, so the entire app's state is just files on disk that you own and can back up, inspect, or delete yourself.
- **Local retrieval, not a hosted vector DB.** `rag.py` lets you upload PDFs and chat with them. Instead of calling out to a hosted embeddings API, it chunks each PDF and ranks relevance with scikit-learn's TF-IDF + cosine similarity — a lightweight, fully local retrieval method that needs no GPU and no external service.
- **Local speech, not a cloud speech API.** `voice.py` transcribes microphone input using `faster-whisper` running locally, and playback uses the browser's built-in speech synthesis — again, nothing sent off-device.
- **Notifications are opt-in and explicit.** `notifications.py` only sends email/SMS if you configure SMTP or Twilio credentials yourself in `.env`; if you don't, it just logs to the console so the app still works fully offline.

The result is an assistant with the *interaction model* of a modern hosted AI product (streaming replies, chat history, a polished composer, quick-action prompts) but the *trust model* of software you actually control.

---

## Features

- 💬 **Streaming chat** with a local Llama model via Ollama
- 📄 **Chat with your PDFs** — upload documents and get answers grounded in their content, with source citations
- 🎙️ **Voice input** — record a question and have it transcribed locally with Whisper
- 🔊 **Voice output** — have replies read back to you
- 🗂️ **Conversation history** — every chat is saved per-account and can be revisited, renamed, or deleted
- 🔐 **Local accounts** — sign up, sign in, and reset your password (via emailed/texted one-time codes) without any third-party auth

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        app.py                            │
│   Streamlit UI: auth screen, sidebar, chat, composer      │
└───────┬───────────┬───────────┬────────────┬─────────────┘
        │           │           │            │
        ▼           ▼           ▼            ▼
   auth.py      storage.py    rag.py      voice.py
  (accounts,   (conversation  (PDF chunk-  (speech-to-
   sessions,    persistence   ing + TF-IDF  text via
   password         as         retrieval)   faster-
   resets)        JSON)                     whisper)
        │
        ▼
  notifications.py
  (email/SMS, opt-in
   via .env config)

              llm_backend.py
        (talks to a local Ollama
         process for streaming
         chat completions)
```

Everything is orchestrated from `app.py`, which is the single Streamlit entry point. Each other module is a self-contained piece of functionality with no dependency on Streamlit itself (except `rag.py`, which uses `st.session_state` to cache indexed PDF chunks per session) — so the auth, storage, retrieval, and voice logic could in principle be reused outside of this particular UI.

---

## Getting started

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/download) installed and running locally
- A pulled model — this app defaults to `llama3.2`:
  ```bash
  ollama pull llama3.2
  ```

### Installation

```bash
git clone https://github.com/<your-username>/anythinggpt.git
cd anythinggpt
pip install -r requirements.txt
```

### Configuration (optional)

Notifications (account-creation emails, password-reset codes) are optional. To enable them, copy the example env file and fill in your own credentials:

```bash
cp .env.example .env
```

```
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USER=you@example.com
EMAIL_PASSWORD=your-app-password
EMAIL_FROM=you@example.com

TWILIO_ACCOUNT_SID=xxxx
TWILIO_AUTH_TOKEN=xxxx
TWILIO_FROM_NUMBER=+1xxxxxxxxxx
```

If you skip this step, the app still works — it just prints what *would* have been sent to the console instead of actually sending it.

### Run it

```bash
streamlit run app.py
```

Then open the URL Streamlit prints (typically `http://localhost:8501`), create an account, and start chatting.

---

---

## Data & privacy

- User accounts are stored in `data/users.json` with salted, hashed passwords (plaintext passwords are never stored).
- Conversations are stored per-user in `data/conversations/<username>.json`.
- Uploaded PDFs are chunked and indexed only in memory (`st.session_state`) for the duration of your session — they are not written to disk.
- No data is sent anywhere unless you explicitly configure SMTP/Twilio for notifications; the LLM itself runs locally via Ollama.

---
## Preview
<img width="954" height="434" alt="Screenshot 2026-07-15 213516" src="https://github.com/user-attachments/assets/8c79b6b5-17aa-4b8e-86ce-17bf5d7f6661" />

---

<img width="947" height="431" alt="Screenshot 2026-07-15 214232" src="https://github.com/user-attachments/assets/32619670-1b71-426f-9e22-a352bea4148a" />


---

<img width="949" height="414" alt="Screenshot 2026-07-15 214506" src="https://github.com/user-attachments/assets/385960ca-5ba8-47c9-90a9-48c0be53eb1d" />


---

