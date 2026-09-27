# Voice Input

Arch Linux / Wayland 下的全局按住说话输入工具。按住 F12 录音，松开后在本机运行 FunASR Paraformer Q8，把简体中文转写粘贴到当前焦点应用；不自动发送。

## 功能

- F12 按住录音、松开发送识别任务
- Mako 显示录音状态、随音量变化的波形和识别状态
- 麦克风静音与无输入检测
- 本地 Paraformer Q8 + FSMN-VAD，OpenCC 转简体
- 识别结果用 Wayland 剪贴板粘贴，可用于 Pi 或其他应用

录音只暂存在 `/tmp`，识别完成后删除；音频不会上传。模型与运行时保存在 `~/.local/share/voice-input`，不放入 Git。

## 安装

在 Arch Linux 上从项目根目录运行：

```bash
sudo ./setup-system.sh
./install.sh
```

第一步安装系统依赖并配置 udev 键盘权限；第二步下载固定版本的 FunASR llama.cpp AVX2 运行时和 Paraformer Q8 / FSMN-VAD 模型，部署用户级 systemd 服务与 Mako 配置。模型与运行时初次下载需要网络。需要重新登录时，按提示操作。

安装后按住 F12 说话，松开后文字会粘贴到当前焦点输入框。

## 运行时布局

```text
~/.local/bin/voice-input.py
~/.local/share/voice-input/runtime/llama-funasr-paraformer
~/.local/share/voice-input/models/paraformer-q8.gguf
~/.local/share/voice-input/models/fsmn-vad.gguf
~/.config/systemd/user/voice-input.service
~/.config/mako/config
/etc/udev/rules.d/70-voice-input.rules
```

识别引擎按需启动：模型不会常驻占用数 GB 内存。当前输入设备对应的 udev 规则匹配 Apple SPI 内置键盘与 USB 厂商 ID `060b`；更换键盘时应修改 `udev/70-voice-input.rules.in` 中的匹配条件。

## 诊断

```bash
systemctl --user status voice-input.service
journalctl --user -u voice-input.service -f
```

识别模型与运行时来源、版本和许可说明见 [`docs/model-attribution.md`](docs/model-attribution.md)。
