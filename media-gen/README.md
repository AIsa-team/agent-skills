## OpenClaw Media Gen

使用 AIsa API 生成图片与视频：

- **Gemini 图片**：`gemini-3-pro-image-preview`（`/v1/models/{model}:generateContent`）
- **Wan 2.6 视频**：`wan2.6-t2v`（`/apis/v1/services/aigc/...` 异步任务 + 轮询）

相关 API 文档索引：[`https://docs.aisa.one/reference/introduction`](https://docs.aisa.one/reference/introduction)

### 快速开始

```bash
export AISA_API_KEY="your-key"
```

### 生成图片

```bash
python scripts/media_gen_client.py image \
  --prompt "A cute red panda, cinematic lighting" \
  --out out.png
```

### 生成视频（创建任务 + 轮询）

```bash
python scripts/media_gen_client.py video-create \
  --prompt "cinematic close-up, slow push-in" \
  --img-url "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Cat03.jpg/320px-Cat03.jpg" \
  --duration 5

python scripts/media_gen_client.py video-wait \
  --task-id <task_id> \
  --poll 10 \
  --timeout 600
```

### 自动下载生成的视频（mp4）

```bash
python scripts/media_gen_client.py video-wait \
  --task-id <task_id> \
  --download \
  --out out.mp4
```

