#!/usr/bin/env python3
"""Hold F12 to dictate locally; paste the transcription when released."""
import asyncio
import math
import os
import signal
import subprocess
import tempfile
import wave
from array import array
from pathlib import Path

from evdev import InputDevice, list_devices, ecodes
from opencc import OpenCC
from english_spacing import add_english_spaces

ASSET_DIR = Path.home() / ".local/share/voice-input"
BACKEND = os.environ.get("VOICE_INPUT_BACKEND", "paraformer").strip().lower()
FUNASR_RUNTIME = ASSET_DIR / "runtime/llama-funasr-paraformer"
MODEL = ASSET_DIR / "models/paraformer-q8.gguf"
VAD_MODEL = ASSET_DIR / "models/fsmn-vad.gguf"
FIRERED_MODEL_DIR = ASSET_DIR / "models/sherpa-onnx-fire-red-asr2-ctc-zh_en-int8-2026-02-25"
FIRERED_PYTHON = ASSET_DIR / "firered-venv/bin/python"
FIRERED_SCRIPT = Path(__file__).with_name("recognize_firered.py")
WAVEFORM = "▁▂▃▄▅▆▇█"
TO_SIMPLIFIED = OpenCC("t2s")


def notify(message, timeout=0):
    subprocess.run([
        "notify-send", "-a", "Pi 语音输入", "-t", str(timeout),
        "-h", "string:x-canonical-private-synchronous:voice-input",
        "语音输入", message,
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def keyboards():
    for path in list_devices():
        try:
            dev = InputDevice(path)
            if ecodes.KEY_F12 in dev.capabilities().get(ecodes.EV_KEY, []):
                yield dev
            else:
                dev.close()
        except (OSError, PermissionError):
            continue


def mic_is_muted():
    try:
        status = subprocess.run(
            ["pactl", "get-source-mute", "@DEFAULT_SOURCE@"],
            capture_output=True, text=True, check=True,
        ).stdout.strip().lower()
        return status.endswith("yes")
    except (subprocess.CalledProcessError, OSError):
        return False


def audio_has_signal(path):
    try:
        with wave.open(path, "rb") as audio:
            samples = array("h", audio.readframes(audio.getnframes()))
        if not samples:
            return False
        if os.sys.byteorder != "little":
            samples.byteswap()
        return sum(sample * sample for sample in samples) / len(samples) >= 1600
    except (OSError, wave.Error):
        return False


async def capture_audio(proc, path):
    levels = [0] * 18
    last_update = 0.0
    with wave.open(path, "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(16000)
        while data := await proc.stdout.read(3200):
            output.writeframesraw(data)
            samples = array("h", data[:len(data) - len(data) % 2])
            if os.sys.byteorder != "little":
                samples.byteswap()
            if samples:
                rms = math.sqrt(sum(sample * sample for sample in samples) / len(samples)) / 32768
                db = 20 * math.log10(max(rms, 1e-6))
                level = max(0, min(7, round((db + 55) * 7 / 45)))
                levels.append(level)
                levels.pop(0)
            now = asyncio.get_running_loop().time()
            if now - last_update >= 0.25:
                bars = "".join(WAVEFORM[level] for level in levels)
                notify(f"● 正在录音\n{bars}\n松开 F12 开始转换")
                last_update = now


async def main():
    devices = list(keyboards())
    if not devices:
        notify("找不到可访问的键盘；检查键盘 udev 权限", 4000)
        return
    if BACKEND == "firered":
        if not FIRERED_PYTHON.is_file() or not (FIRERED_MODEL_DIR / "model.int8.onnx").is_file():
            notify("FireRedASR2 模型或运行环境缺失；请重新运行安装脚本", 5000)
            return
    elif BACKEND == "paraformer":
        if not MODEL.exists() or not FUNASR_RUNTIME.exists() or not VAD_MODEL.exists():
            notify("Paraformer 量化模型或运行时文件缺失", 4000)
            return
    else:
        notify(f"未知语音识别后端：{BACKEND}", 5000)
        return

    recording = None
    wav_path = None
    capture_task = None

    async def finish():
        nonlocal recording, wav_path, capture_task
        proc, path, task = recording, wav_path, capture_task
        recording = wav_path = capture_task = None
        proc.send_signal(signal.SIGINT)
        await proc.wait()
        await task
        if mic_is_muted():
            notify("麦克风已静音\n请打开麦克风后重试", 4000)
            Path(path).unlink(missing_ok=True)
            return
        if not audio_has_signal(path):
            notify("麦克风没有收到声音\n请检查静音开关或输入设备", 4000)
            Path(path).unlink(missing_ok=True)
            return
        notify("正在本机识别…\n请稍候")
        try:
            if BACKEND == "firered":
                command = [str(FIRERED_PYTHON), str(FIRERED_SCRIPT), path]
            else:
                command = [str(FUNASR_RUNTIME), "-m", str(MODEL), "--vad", str(VAD_MODEL), "-a", path]
            result = subprocess.run(command, capture_output=True, text=True, check=True).stdout.strip()
            result = add_english_spaces(TO_SIMPLIFIED.convert(result))
            if result:
                subprocess.run(["wl-copy", "--type", "text/plain;charset=utf-8"], input=result, text=True, check=True)
                await asyncio.sleep(0.12)
                subprocess.run(["wtype", "-M", "ctrl", "v", "-m", "ctrl"], check=True)
                notify("已粘贴到当前输入框", 2200)
            else:
                notify("没有识别到语音", 2500)
        except (subprocess.CalledProcessError, OSError) as exc:
            notify(f"识别或粘贴失败：{exc}", 4000)
        finally:
            Path(path).unlink(missing_ok=True)

    queue = asyncio.Queue()

    async def read_device(dev):
        async for event in dev.async_read_loop():
            await queue.put(event)

    notify("就绪：按住 F12 说话", 2200)
    readers = [asyncio.create_task(read_device(dev)) for dev in devices]
    try:
        while True:
            event = await queue.get()
            if event.type != ecodes.EV_KEY or event.code != ecodes.KEY_F12:
                continue
            if event.value == 1 and recording is None:
                fd, wav_path = tempfile.mkstemp(prefix="pi-voice-", suffix=".wav")
                os.close(fd)
                recording = await asyncio.create_subprocess_exec(
                    "pw-record", "--rate", "16000", "--channels", "1", "--format", "s16", "-",
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
                )
                capture_task = asyncio.create_task(capture_audio(recording, wav_path))
                notify("● 正在录音\n松开 F12 开始转换")
            elif event.value == 0 and recording is not None:
                await finish()
    finally:
        for task in readers:
            task.cancel()
        for dev in devices:
            dev.close()
        if recording:
            recording.terminate()
            await recording.wait()
            if capture_task:
                await capture_task
            Path(wav_path).unlink(missing_ok=True)


if __name__ == "__main__":
    asyncio.run(main())
