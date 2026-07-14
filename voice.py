from tempfile import NamedTemporaryFile


def transcribe_audio(audio):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return "", "Voice transcription needs faster-whisper. Install the requirements, then restart Streamlit."
    try:
        with NamedTemporaryFile(suffix=".wav", delete=False) as temp:
            temp.write(audio.getvalue())
            path = temp.name
        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, _ = model.transcribe(path, beam_size=3)
        return " ".join(segment.text.strip() for segment in segments), None
    except Exception as exc:
        return "", f"Couldn't transcribe audio: {exc}"
