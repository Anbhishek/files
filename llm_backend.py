import subprocess

try:
    from ollama import chat as ollama_chat
except ModuleNotFoundError:  # pragma: no cover - runtime fallback
    ollama_chat = None

SYSTEM_PROMPT = """You are AnythingGPT, a helpful, accurate private assistant.
If document context is supplied, use it as your primary source."""


def _build_system(document_context: str = "") -> str:
    system = SYSTEM_PROMPT
    if document_context:
        system += "\n\nRelevant excerpts from the user's PDFs:\n" + document_context
    return system


def ask_llm_stream(messages, document_context: str = ""):
    """Yield the assistant reply incrementally so the UI can stream it, Claude-style."""
    system = _build_system(document_context)
    try:
        if ollama_chat is not None:
            stream = ollama_chat(
                model="llama3.2",
                messages=[{"role": "system", "content": system}, *messages],
                stream=True,
            )
            got_any = False
            for chunk in stream:
                token = chunk.get("message", {}).get("content", "")
                if token:
                    got_any = True
                    yield token
            if not got_any:
                yield "⚠️ Ollama returned an empty response."
            return

        # No python client installed: fall back to the CLI (non-streaming).
        prompt = f"{system}\n\nUser conversation:\n"
        for message in messages:
            prompt += f"{message['role']}: {message['content']}\n"

        result = subprocess.run(
            ["ollama", "run", "llama3.2"],
            input=prompt,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())
        yield result.stdout.strip()
    except Exception as exc:
        yield (
            "⚠️ I couldn't reach Ollama. Make sure it is running and "
            f"`ollama pull llama3.2` has completed.\n\nDetails: `{exc}`"
        )


def ask_llm(messages, document_context: str = "") -> str:
    """Non-streaming convenience wrapper kept for callers that want the full text at once."""
    return "".join(ask_llm_stream(messages, document_context))
