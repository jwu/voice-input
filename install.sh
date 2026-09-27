#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DATA="$HOME/.local/share/voice-input"
RUNTIME="$DATA/runtime"
MODELS="$DATA/models"
RELEASE="https://github.com/modelscope/FunASR/releases/download/runtime-llamacpp-v0.2.6/funasr-llamacpp-linux-x64-avx2.tar.gz"

if [[ ! -r /etc/arch-release ]]; then
  echo "This installer currently supports Arch Linux only." >&2
  exit 1
fi

for command in ffmpeg wtype wl-copy notify-send mako curl setfacl; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "Missing system dependency: $command. Run sudo ./setup-system.sh first." >&2
    exit 1
  fi
done
if ! /usr/bin/python3 -c 'import evdev, opencc' >/dev/null 2>&1; then
  echo "Missing Python modules. Run sudo ./setup-system.sh first." >&2
  exit 1
fi

mkdir -p "$RUNTIME" "$MODELS" "$HOME/.local/bin" "$HOME/.config/systemd/user" "$HOME/.config/mako"

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

install -Dm755 "$ROOT/src/voice_input.py" "$HOME/.local/bin/voice-input.py"
install -Dm644 "$ROOT/systemd/user/voice-input.service" "$HOME/.config/systemd/user/voice-input.service"
install -Dm644 "$ROOT/mako/config" "$HOME/.config/mako/config"

trap 'rm -f "${archive:-}"' EXIT

for old in pi-voice-input.service pi-funasr-server.service pi-whisper-server.service; do
  systemctl --user disable --now "$old" >/dev/null 2>&1 || true
done
systemctl --user daemon-reload
systemctl --user enable --now mako.service voice-input.service

echo "Voice Input installed. Hold F12 to dictate."
