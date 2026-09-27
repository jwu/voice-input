#!/usr/bin/env python3
"""Transcribe a 16 kHz mono PCM WAV with FireRedASR2 CTC via sherpa-onnx."""
import sys
import wave
from array import array
from pathlib import Path

import numpy as np
import sherpa_onnx

MODEL_DIR = (
    Path.home()
    / ".local/share/voice-input/models/sherpa-onnx-fire-red-asr2-ctc-zh_en-int8-2026-02-25"
)


def main():
    if len(sys.argv) != 2:
        raise SystemExit(f"Usage: {sys.argv[0]} AUDIO.wav")

    with wave.open(sys.argv[1], "rb") as audio:
        if audio.getnchannels() != 1 or audio.getframerate() != 16000 or audio.getsampwidth() != 2:
            raise ValueError("Expected 16 kHz mono 16-bit PCM WAV")
        samples = array("h", audio.readframes(audio.getnframes()))
    if sys.byteorder != "little":
        samples.byteswap()

    recognizer = sherpa_onnx.OfflineRecognizer.from_fire_red_asr_ctc(
        model=str(MODEL_DIR / "model.int8.onnx"),
        tokens=str(MODEL_DIR / "tokens.txt"),
        num_threads=2,
        decoding_method="greedy_search",
        provider="cpu",
    )
    stream = recognizer.create_stream()
    stream.accept_waveform(16000, np.asarray(samples, dtype=np.float32) / 32768.0)
    recognizer.decode_stream(stream)
    print(stream.result.text)


if __name__ == "__main__":
    main()
