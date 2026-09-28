#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DATA="$HOME/.local/share/voice-input"
RUNTIME="$DATA/runtime"
MODELS="$DATA/models"
FIRERED_ENV="$DATA/firered-venv"
FIRERED_MODEL="sherpa-onnx-fire-red-asr2-ctc-zh_en-int8-2026-02-25"
FIRERED_RELEASE="https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/$FIRERED_MODEL.tar.bz2"
RELEASE="https://github.com/modelscope/FunASR/releases/download/runtime-llamacpp-v0.2.6/funasr-llamacpp-linux-x64-avx2.tar.gz"

if [[ ! -r /etc/arch-release ]]; then
  echo "This installer currently supports Arch Linux only." >&2
  exit 1
fi

for command in pw-record wtype wl-copy notify-send mako curl setfacl; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "Missing system dependency: $command. Run sudo ./setup-system.sh first." >&2
    exit 1
  fi
done
if ! /usr/bin/python3 -c 'import evdev, opencc' >/dev/null 2>&1; then
  echo "Missing Python modules. Run sudo ./setup-system.sh first." >&2
  exit 1
fi

mkdir -p "$RUNTIME" "$MODELS" "$HOME/.local/bin" "$HOME/.config/systemd/user" "$HOME/.config/mako" "$HOME/.config/voice-input"

if [[ ! -x "$RUNTIME/llama-funasr-paraformer" ]]; then
  archive="$(mktemp)"
  trap 'rm -f "$archive"' EXIT
  curl -fL --retry 2 "$RELEASE" -o "$archive"
  tar -xzf "$archive" -C "$RUNTIME"
fi

fetch_if_missing() {
  local url="$1" destination="$2" temporary
  [[ -s "$destination" ]] && return 0
  temporary="$(mktemp "${destination}.XXXXXX")"
  curl -fL --retry 2 "$url" -o "$temporary"
  mv "$temporary" "$destination"
}

fetch_if_missing \
  "https://huggingface.co/FunAudioLLM/Paraformer-GGUF/resolve/main/paraformer-q8.gguf" \
  "$MODELS/paraformer-q8.gguf"
fetch_if_missing \
  "https://huggingface.co/FunAudioLLM/fsmn-vad-GGUF/resolve/main/fsmn-vad.gguf" \
  "$MODELS/fsmn-vad.gguf"

if [[ ! -s "$MODELS/$FIRERED_MODEL/model.int8.onnx" ]]; then
  archive="$(mktemp)"
  trap 'rm -f "$archive"' EXIT
  curl -fL --retry 2 "$FIRERED_RELEASE" -o "$archive"
  tar -xjf "$archive" -C "$MODELS"
  rm -f "$archive"
fi
python3 -m venv "$FIRERED_ENV"
"$FIRERED_ENV/bin/python" -m pip install --disable-pip-version-check \
  'sherpa-onnx==1.13.2' 'numpy>=1.26,<3' 'opencc==1.4.1'

if [[ ! -e "$HOME/.config/voice-input/config" ]]; then
  printf 'VOICE_INPUT_BACKEND=paraformer\n' > "$HOME/.config/voice-input/config"
fi
install -Dm755 "$ROOT/src/voice_input.py" "$HOME/.local/bin/voice-input.py"
install -Dm644 "$ROOT/src/english_spacing.py" "$HOME/.local/bin/english_spacing.py"
install -Dm644 "$ROOT/src/vendor/wordninja.py" "$HOME/.local/bin/vendor/wordninja.py"
install -Dm644 "$ROOT/src/vendor/wordninja/wordninja_words.txt.gz" "$HOME/.local/bin/vendor/wordninja/wordninja_words.txt.gz"
install -Dm644 "$ROOT/src/vendor/wordninja/LICENSE" "$HOME/.local/bin/vendor/wordninja/LICENSE"
install -Dm755 "$ROOT/src/recognize_firered.py" "$HOME/.local/bin/recognize_firered.py"
install -Dm644 "$ROOT/systemd/user/voice-input.service" "$HOME/.config/systemd/user/voice-input.service"
install -Dm644 "$ROOT/mako/config" "$HOME/.config/mako/config"

trap 'rm -f "${archive:-}"' EXIT

for old in pi-voice-input.service pi-funasr-server.service pi-whisper-server.service; do
  systemctl --user disable --now "$old" >/dev/null 2>&1 || true
done
systemctl --user daemon-reload
systemctl --user enable --now mako.service voice-input.service
systemctl --user restart voice-input.service

echo "Voice Input installed. Hold F12 to dictate."
