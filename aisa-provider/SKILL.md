---
name: aisa-provider
description: Configure AIsa as a first-class model provider for OpenClaw, enabling production access to major Chinese AI models (Qwen, DeepSeek, Kimi K2.5, Doubao) through official partnerships with Alibaba Cloud, BytePlus, and Moonshot. Use this skill when the user wants to set up Chinese AI models, configure AIsa API access, compare pricing between AIsa and other providers (OpenRouter, Bailian), switch between Qwen/DeepSeek/Kimi models, or troubleshoot AIsa provider configuration in OpenClaw. Also use when the user mentions AISA_API_KEY, asks about Chinese LLM pricing, Kimi K2.5 setup, or needs help with Qwen Key Account setup.
compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries curl, openclaw, environment variables AISA_API_KEY and internet access to api.aisa.one.
metadata:
  aisa:
    emoji: 🇨🇳
    requires:
      bins:
      - curl
      - openclaw
      env:
      - AISA_API_KEY
    primaryEnv: AISA_API_KEY
    compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries curl, openclaw, environment variables AISA_API_KEY and internet access to api.aisa.one.
---

# AIsa Provider for OpenClaw

AIsa is a unified API gateway providing production access to China's leading AI models through official partnerships with all major Chinese AI platforms. It is an Alibaba Cloud Qwen Key Account partner, offering the full Qwen model family at discounted pricing, plus models on the Alibaba Bailian aggregation platform (DeepSeek, Kimi, GLM).

AIsa also provides access to **Kimi K2.5** (Moonshot AI's flagship reasoning model) at approximately **80% of official pricing**.

> ⚠️ All pricing listed below is for reference. Real-time pricing is subject to change — always check https://marketplace.aisa.one/pricing for the latest rates.

## Quick Setup

### Option 1: Environment Variable (fastest)

```bash
export AISA_API_KEY="your-key-here"
```

OpenClaw auto-detects `AISA_API_KEY` and registers AIsa as a provider. No config file changes needed.

### Option 2: Interactive Onboarding

```bash
openclaw onboard --auth-choice aisa-api-key
```

### Option 3: CLI with Key

```bash
openclaw onboard --auth-choice aisa-api-key --aisa-api-key "your-key-here"
```

### Option 4: Manual Config in `~/.openclaw/openclaw.json`

```json
{
  "models": {
    "providers": {
      "aisa": {
        "baseUrl": "https://api.aisa.one/v1",
        "apiKey": "${AISA_API_KEY}",
        "api": "openai-completions",
        "models": [
          {
            "id": "aisa/qwen3-max",
            "name": "Qwen3 Max",
            "reasoning": true,
            "input": ["text", "image"],
            "contextWindow": 256000,
            "maxTokens": 16384,
            "supportsDeveloperRole": false,
            "cost": {
              "input": 1.20,
              "output": 4.80,
              "cacheRead": 0,
              "cacheWrite": 0
            }
          },
          {
            "id": "aisa/qwen-plus-2025-12-01",
            "name": "Qwen Plus",
            "reasoning": true,
            "input": ["text", "image"],
            "contextWindow": 256000,
            "maxTokens": 16384,
            "supportsDeveloperRole": false,
            "cost": {
              "input": 0.30,
              "output": 0.90,
              "cacheRead": 0,
              "cacheWrite": 0
            }
          },
          {
            "id": "aisa/qwen-mt-flash",
            "name": "Qwen MT Flash",
            "reasoning": true,
            "input": ["text"],
            "contextWindow": 256000,
            "maxTokens": 8192,
            "supportsDeveloperRole": false,
            "cost": {
              "input": 0.05,
              "output": 0.30,
              "cacheRead": 0,
              "cacheWrite": 0
            }
          },
          {
            "id": "aisa/deepseek-v3.1",
            "name": "DeepSeek V3.1",
            "reasoning": true,
            "input": ["text"],
            "contextWindow": 131072,
            "maxTokens": 8192,
            "supportsDeveloperRole": false,
            "cost": {
              "input": 0.27,
              "output": 1.10,
              "cacheRead": 0.07,
              "cacheWrite": 0
            }
          },
          {
            "id": "aisa/kimi-k2.5",
            "name": "Kimi K2.5",
            "reasoning": true,
            "input": ["text"],
            "contextWindow": 131072,
            "maxTokens": 8192,
            "supportsDeveloperRole": false,
            "cost": {
              "input": 0.60,
              "output": 2.40,
              "cacheRead": 0,
              "cacheWrite": 0
            }
          }
        ]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "aisa/qwen3-max"
      }
    }
  }
}
```

## Available Models

### Default Models (pre-configured, API-verified ✅)

| Model | Model ID | Best For | Context | Reasoning | Verified |
|-------|----------|----------|---------|-----------|----------|
| Qwen3 Max | `aisa/qwen3-max` | Complex reasoning, flagship tasks | 256K | ✅ | ✅ |
| Qwen Plus | `aisa/qwen-plus-2025-12-01` | Main production model | 256K | ✅ | ✅ |
| Qwen MT Flash | `aisa/qwen-mt-flash` | High-frequency, lightweight tasks | 256K | ✅ | ✅ |
| DeepSeek V3.1 | `aisa/deepseek-v3.1` | Cost-effective reasoning | 128K | ✅ | ✅ |
| **Kimi K2.5** | `aisa/kimi-k2.5` | **Moonshot's flagship reasoning model** | 128K | ✅ | ✅ |

### ⭐ Kimi K2.5 — Moonshot AI's Flagship Model

Kimi K2.5 is Moonshot AI's latest reasoning model, accessible via AIsa at approximately **80% of official Moonshot pricing**.

**Key features:**
- Strong reasoning and multi-step problem solving
- Competitive performance on coding and math benchmarks
- Available through AIsa's Moonshot partnership

#### 🔒 Zero Data Retention (ZDR) — Enterprise-Grade Privacy

Accessing Kimi K2.5 through AIsa comes with **enterprise-level Zero Data Retention** guarantees. Users do not need to worry about data privacy — AIsa has executed a formal ZDR agreement with Moonshot AI.

Under the **Supplemental Enterprise Service Agreement** (dated 10 February 2026) between AIsa and Kimi (Moonshot AI PTE. LTD.):

- **Customer data is NOT retained** by Moonshot after processing
- **Generated outputs are NOT stored** on Moonshot's infrastructure
- **No data is used for model training** — your prompts and completions remain private
- Processing is governed by contractual enterprise terms, not consumer ToS

This makes AIsa the recommended path for privacy-sensitive or enterprise workloads that require access to Kimi K2.5. When calling Kimi K2.5 directly via Moonshot's consumer API, standard consumer data policies apply — by routing through AIsa, your data benefits from the negotiated ZDR protections.

**⚠️ Important: Temperature restriction**

Kimi K2.5 **only accepts `temperature=1.0`**. Using any other value will return an error:
```
Error: invalid temperature: only 1 is allowed for this model
```

If your OpenClaw config or agent sets a different temperature, override it for Kimi:
```
/model aisa/kimi-k2.5
```
OpenClaw will use the model's default temperature when not explicitly set.

**Kimi K2.5 Pricing Comparison (per 1M tokens):**

| Metric | AIsa | Moonshot Official | Savings |
|--------|------|-------------------|---------|
| Input/1M | ~$0.60 | ~$0.75 | ~20% off |
| Output/1M | ~$2.40 | ~$3.00 | ~20% off |

> Actual pricing may vary. Check https://marketplace.aisa.one/pricing for real-time rates.

### Additional Models Available via AIsa

Users can add any model supported by AIsa to their config. The full catalog includes **49+ models**:

**Qwen family (8 models):**
- `qwen3-max`, `qwen3-max-2026-01-23`, `qwen-plus-2025-12-01`
- `qwen-mt-flash`, `qwen-mt-lite`
- `qwen-vl-max`, `qwen3-vl-flash`, `qwen3-vl-plus` (vision models)

**DeepSeek (4 models):**
- `deepseek-v3.1`, `deepseek-v3`, `deepseek-v3-0324`, `deepseek-r1`

**Kimi / Moonshot (2 models):**
- `kimi-k2.5`, `kimi-k2-thinking`

**Also available:** Claude series (10), GPT series (9), Gemini series (5), Grok series (2), and more.

**List all available models:**
```bash
curl https://api.aisa.one/v1/models -H "Authorization: Bearer $AISA_API_KEY"
```

## Model ID Versioning

AIsa uses **versioned model IDs** for some models. If you encounter a `503 - No available channels` error, the model ID may need updating.

**Known model ID mappings:**

| Common Name | Correct AIsa Model ID | ❌ Does NOT work |
|-------------|----------------------|------------------|
| Qwen Plus | `qwen-plus-2025-12-01` | `qwen3-plus`, `qwen-plus`, `qwen-plus-latest` |
| Qwen Flash | `qwen-mt-flash` | `qwen3-flash`, `qwen-turbo`, `qwen-turbo-latest` |
| Qwen Max | `qwen3-max` | (works as-is) |
| DeepSeek V3.1 | `deepseek-v3.1` | (works as-is) |
| Kimi K2.5 | `kimi-k2.5` | (works as-is) |

To check the latest available model IDs:
```bash
curl https://api.aisa.one/v1/models -H "Authorization: Bearer $AISA_API_KEY"
```

## Switching Models

In chat (TUI):

```
/model aisa/qwen3-max
/model aisa/deepseek-v3.1
/model aisa/kimi-k2.5
```

Via CLI:

```bash
openclaw models set aisa/qwen3-max
```

## Pricing Comparison (per 1M tokens)

> All pricing below is for reference. Real-time pricing is subject to change — always check https://marketplace.aisa.one/pricing for the latest rates.

### Qwen MT Flash (lightweight)
- **AIsa**: $0.05 input / $0.30 output (**~50% off** retail)
- Bailian Official: $0.10 / $0.40
- OpenRouter: $0.11-0.13 / $0.45-0.50

### Qwen Plus (production)
- **AIsa**: $0.30 input / $0.90 output (**~25% off** retail)
- Bailian Official: $0.40 / $1.20
- OpenRouter: $0.45-0.50 / $1.35-1.50

### Qwen3 Max (flagship)
- **AIsa**: $1.20 input / $4.80 output (**~40% off** retail)
- Bailian Official: $2.00 / $8.00
- OpenRouter: $2.20-2.50 / $9.00-10.00

### Kimi K2.5 (Moonshot flagship)
- **AIsa**: ~$0.60 input / ~$2.40 output (**~20% off** official Moonshot pricing)
- Moonshot Official: ~$0.75 / ~$3.00
- OpenRouter: Limited availability

### Cost at scale: 500M tokens/month on Qwen-Max
- OpenRouter: ~$4,000-4,250/month
- Bailian Official: ~$3,400/month
- AIsa: ~$2,040/month (**saves $16,320-26,520/year**)

## Official Partnerships

AIsa maintains verified partnerships with:
- **Alibaba Cloud** — Qwen Key Account (full model family, 3 global regions: CN, US-Virginia, Singapore)
- **BytePlus** — Doubao by ByteDance
- **DeepSeek** — via Alibaba Cloud integration
- **Moonshot** — Kimi K2.5 integration, with **enterprise Zero Data Retention (ZDR) agreement** (effective Feb 10, 2026)

## Qwen Region Support

AIsa provides access to Qwen models across 3 global regions via Alibaba Cloud:
- 🇨🇳 China (default)
- 🇺🇸 US (Virginia)
- 🇸🇬 Singapore

This is unique to AIsa's Key Account status. Other providers like OpenRouter or the free Qwen Portal typically route through CN only.

## Response Latency (tested Feb 2026)

| Model | Avg Latency | Rating |
|-------|-------------|--------|
| Qwen3 Max | ~1,577 ms | ⭐⭐⭐⭐⭐ Fastest |
| Qwen MT Flash | ~1,918 ms | ⭐⭐⭐⭐ Fast |
| Kimi K2.5 | ~2,647 ms | ⭐⭐⭐ Medium |
| DeepSeek V3.1 | ~3,002 ms | ⭐⭐⭐ Medium |
| Qwen Plus | ~8,207 ms | ⭐⭐ Slower |

## Troubleshooting

### "503 - No available channels" error
The model ID may be incorrect or outdated. Check the **Model ID Versioning** section above for correct IDs. Common fixes:
- `qwen3-plus` → use `qwen-plus-2025-12-01`
- `qwen3-flash` → use `qwen-mt-flash`

### "Model not found" error
Ensure the model ID uses the `aisa/` prefix in OpenClaw config:
```
✅ aisa/qwen3-max
❌ qwen3-max
```

### Kimi K2.5 "invalid temperature" error
Kimi K2.5 only accepts `temperature=1.0`. If your config sets a different temperature, add a model-specific override or let OpenClaw use the default.

### Kimi K2.5 empty response
In rare cases Kimi K2.5 may return empty content while consuming output tokens. Retry the request — this is typically transient.

### API key not detected
1. Check env var: `echo $AISA_API_KEY`
2. Or verify in config: `openclaw config get auth.profiles`
3. Re-run onboarding: `openclaw onboard --auth-choice aisa-api-key`

### Streaming not working
AIsa uses the OpenAI-compatible API (`openai-completions`). Ensure your config has:
```json
"api": "openai-completions"
```

### Rate limits or daily caps
AIsa has **no daily request limits** (unlike the free Qwen Portal which caps at 2,000 req/day).

## Get an API Key

1. Visit https://marketplace.aisa.one/
2. Sign up and create an API key
3. Set it as `AISA_API_KEY` or use the onboarding wizard

## Notes

- AIsa's endpoint is OpenAI-compatible (`https://api.aisa.one/v1`)
- All models support streaming and function calling
- `supportsDeveloperRole` is set to `false` for Qwen models
- Default context window: 256,000 tokens (Qwen) or 131,072 tokens (DeepSeek/Kimi)
- Reasoning (thinking) is enabled for all default models
- Kimi K2.5 requires `temperature=1.0` — other values cause API errors
- Kimi K2.5 via AIsa is covered by enterprise Zero Data Retention (ZDR) — data is not retained or used for training
- Image/Video generation models (WAN) are available but require separate configuration
- AIsa API supports 49+ models total — use the models endpoint to discover all available options
