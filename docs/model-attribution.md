# 模型与运行时来源

可选识别后端 FireRedASR2 CTC INT8，通过 sherpa-onnx 在 CPU 上推理：

- 上游模型：FireRedASR2-AED（仅导出 encoder 与 CTC 分支，不使用 attention decoder）
- 转换模型：`sherpa-onnx-fire-red-asr2-ctc-zh_en-int8-2026-02-25`
- sherpa-onnx 模型发布页：<https://github.com/k2-fsa/sherpa-onnx/releases/tag/asr-models>
- 转换说明：<https://huggingface.co/FireRedTeam/FireRedASR2-AED>
- 推理运行时：<https://github.com/k2-fsa/sherpa-onnx>

转换模型权重由 sherpa-onnx 项目发布；上游 README 说明它由 FireRedASR2-AED 导出 encoder 与 CTC 分支。FireRedASR2 模型权重有独立许可，使用前应阅读上游许可与模型卡。

默认识别后端为 Paraformer：

- 转写模型：`FunAudioLLM/Paraformer-GGUF`，文件 `paraformer-q8.gguf`
- 上游模型：`iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch`
- VAD 模型：`FunAudioLLM/fsmn-vad-GGUF`，文件 `fsmn-vad.gguf`
- C++ 运行时：FunASR llama.cpp runtime `v0.2.6`
- FunASR 项目：<https://github.com/modelscope/FunASR>

FunASR 工具包源码采用 MIT 许可；模型权重有独立许可。FunASR 模型许可要求注明来源和作者，并保留模型名称。使用或分发权重前应阅读当前上游许可：<https://github.com/modelscope/FunASR/blob/main/MODEL_LICENSE>。

英文连写空格恢复使用 vendored `wordninja` 2.0.0 与其 Wikipedia unigram 词频表：<https://github.com/keredson/wordninja>。代码及词表采用 MIT 许可，许可证随文件保存在 `src/vendor/wordninja/LICENSE`。

模型与运行时由 `install.sh` 下载至 `~/.local/share/voice-input`；词频模型随源码分发。大型语音模型不提交进本仓库。
