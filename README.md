# Voice Input

Arch Linux / Wayland 下的全局按住说话输入工具。按住 F12 录音，松开后在本机运行 Paraformer Q8，把简体中文转写粘贴到当前焦点应用；不自动发送。FireRedASR2 CTC INT8 仍可切换使用。

## 功能

- F12 按住录音、松开发送识别任务
- Mako 显示录音状态、随音量变化的波形和识别状态
- 麦克风静音与无输入检测
- 本地 Paraformer Q8 + FSMN-VAD，OpenCC 转简体
- 保留 FireRedASR2 CTC INT8（Sherpa-ONNX CPU 推理），可通过配置切换
- 尝试为连写的英文补空格（词频分词；专有名词或歧义句可能切错）
- 识别结果用 Wayland 剪贴板粘贴，可用于 Pi 或其他应用

录音只暂存在 `/tmp`，识别完成后删除；音频不会上传。模型与运行时保存在 `~/.local/share/voice-input`，不放入 Git。

## 安装

在 Arch Linux 上从项目根目录运行：

```bash
sudo ./setup-system.sh
./install.sh
```

第一步安装系统依赖并配置 udev 键盘权限；第二步下载 FireRedASR2 CTC INT8 模型，创建独立 Python 运行环境，并下载 Paraformer Q8 / FSMN-VAD 与 FunASR llama.cpp AVX2 运行时；随后部署用户级 systemd 服务与 Mako 配置。初次安装需要网络。需要重新登录时，按提示操作。

安装后按住 F12 说话，松开后文字会粘贴到当前焦点输入框。

## 选择识别后端

默认使用 Paraformer。英文空格恢复使用 vendored 的 wordninja（MIT）词频模型，离线运行，不会再调用识别模型。编辑 `~/.config/voice-input/config` 并设置后端，然后重启服务：

```bash
VOICE_INPUT_BACKEND=firered
# 或切回原后端：VOICE_INPUT_BACKEND=paraformer
systemctl --user restart voice-input.service
```

识别在本机运行；录音只暂存在 `/tmp`，不会上传。

## 运行时布局

```text
~/.local/bin/voice-input.py
~/.local/bin/recognize_firered.py
~/.local/share/voice-input/firered-venv/
~/.local/share/voice-input/models/sherpa-onnx-fire-red-asr2-ctc-zh_en-int8-2026-02-25/
~/.config/voice-input/config
~/.local/share/voice-input/runtime/llama-funasr-paraformer
~/.local/share/voice-input/models/paraformer-q8.gguf
~/.local/share/voice-input/models/fsmn-vad.gguf
~/.config/systemd/user/voice-input.service
~/.config/mako/config
/etc/udev/rules.d/70-voice-input.rules
```

识别引擎按需启动：模型不会常驻占用数 GB 内存。udev 规则按设备名授权（当前为 `ASUSTeK ROG OMNI RECEIVER Keyboard`、`MOSART Semi. wireless dongle`，另有一条 Apple SPI 内置键盘规则）；更换键盘时用 `udevadm info --attribute-walk --name=/dev/input/eventN | grep name` 查到新设备名，改 `udev/70-voice-input.rules.in` 后重新执行 `sudo ./setup-system.sh`。

## 诊断

```bash
systemctl --user status voice-input.service
journalctl --user -u voice-input.service -f
```

识别模型与运行时来源、版本和许可说明见 [`docs/model-attribution.md`](docs/model-attribution.md)。
