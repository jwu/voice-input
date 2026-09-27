# 模型与运行时来源

当前项目使用 FunASR 的 Paraformer Q8 GGUF 模型及 FSMN-VAD：

- 转写模型：`FunAudioLLM/Paraformer-GGUF`，文件 `paraformer-q8.gguf`
- 上游模型：`iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch`
- VAD 模型：`FunAudioLLM/fsmn-vad-GGUF`，文件 `fsmn-vad.gguf`
- C++ 运行时：FunASR llama.cpp runtime `v0.2.6`
- FunASR 项目：<https://github.com/modelscope/FunASR>

FunASR 工具包源码采用 MIT 许可；模型权重有独立许可。FunASR 模型许可要求注明来源和作者，并保留模型名称。使用或分发权重前应阅读当前上游许可：<https://github.com/modelscope/FunASR/blob/main/MODEL_LICENSE>。

运行时与模型由 `install.sh` 下载到用户数据目录，不提交进本仓库。
