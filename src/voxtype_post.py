#!/usr/bin/env python3
"""Voxtype post-process filter: restore spaces in concatenated English ASR output.

Reads the transcribed text on stdin and writes the processed text on stdout, so it
can be wired into voxtype via [output.post_process] in ~/.config/voxtype/config.toml.

Reuses the english_spacing module (vendored wordninja word-frequency model) that
shipped with voice-input. CJK text is left untouched; only runs of 7+ ASCII letters
are candidates for re-segmentation.
"""
import sys

from english_spacing import add_english_spaces


def main() -> None:
    sys.stdout.write(add_english_spaces(sys.stdin.read()))


if __name__ == "__main__":
    main()
