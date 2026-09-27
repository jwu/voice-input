#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
USER_NAME="${SUDO_USER:-}"

if [[ "$EUID" -ne 0 || -z "$USER_NAME" || "$USER_NAME" == root ]]; then
  echo "Run this script with sudo from the target user's session: sudo ./setup-system.sh" >&2
  exit 1
fi
if [[ ! -r /etc/arch-release ]]; then
  echo "This setup script currently supports Arch Linux only." >&2
  exit 1
fi

pacman -S --needed ffmpeg wtype wl-clipboard opencc python-evdev libnotify mako acl curl
rule="$(mktemp)"
trap 'rm -f "$rule"' EXIT
sed "s/@USER@/$USER_NAME/g" "$ROOT/udev/70-voice-input.rules.in" > "$rule"
install -Dm644 "$rule" /etc/udev/rules.d/70-voice-input.rules
udevadm control --reload-rules
udevadm trigger --action=add --subsystem-match=input
udevadm settle
