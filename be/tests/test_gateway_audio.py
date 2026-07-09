import wave
import io

from app.agent.gateway import _pcm16_to_wav


def test_pcm16_to_wav_produces_valid_wav_with_expected_params():
    pcm_bytes = b"\x00\x01" * 100  # 100 frames of fake 16-bit mono audio

    wav_bytes = _pcm16_to_wav(pcm_bytes, sample_rate=24000, channels=1)

    with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getsampwidth() == 2
        assert wav_file.getframerate() == 24000
        assert wav_file.readframes(wav_file.getnframes()) == pcm_bytes


def test_pcm16_to_wav_respects_custom_sample_rate_and_channels():
    pcm_bytes = b"\x00\x01\x02\x03" * 50

    wav_bytes = _pcm16_to_wav(pcm_bytes, sample_rate=16000, channels=2)

    with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
        assert wav_file.getnchannels() == 2
        assert wav_file.getframerate() == 16000
