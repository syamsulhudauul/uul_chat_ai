import asyncio


async def transcode_to_wav(input_bytes: bytes) -> bytes:
    """Transcode arbitrary audio (e.g. the browser's MediaRecorder webm/opus
    output) to WAV via ffmpeg. Gemini's audio input only accepts
    wav/mp3/aiff/aac/ogg/flac — not webm — so voice mode needs this before
    handing audio to the LLM gateway for transcription.
    """
    process = await asyncio.create_subprocess_exec(
        "ffmpeg",
        "-i", "pipe:0",
        "-f", "wav",
        "-ar", "16000",
        "-ac", "1",
        "pipe:1",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate(input=input_bytes)

    if process.returncode != 0:
        raise RuntimeError(f"ffmpeg transcode failed: {stderr.decode(errors='replace')}")

    return stdout
