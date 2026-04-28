# AIsa Provider Configuration Examples

## Minimal Config (env var auto-detection)

No config needed. Just set the environment variable:

```bash
export AISA_API_KEY="sk-aisa-xxxxx"
```

OpenClaw will auto-detect and register AIsa as a provider.

## Production Config with Fallback Chain

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
            "cost": { "input": 1.20, "output": 4.80 }
          },
          {
            "id": "aisa/qwen-plus-2025-12-01",
            "name": "Qwen Plus",
            "reasoning": true,
            "input": ["text", "image"],
            "contextWindow": 256000,
            "maxTokens": 16384,
            "supportsDeveloperRole": false,
            "cost": { "input": 0.30, "output": 0.90 }
          },
          {
            "id": "aisa/qwen-mt-flash",
            "name": "Qwen MT Flash",
            "reasoning": true,
            "input": ["text"],
            "contextWindow": 256000,
            "maxTokens": 8192,
            "supportsDeveloperRole": false,
            "cost": { "input": 0.05, "output": 0.30 }
          },
          {
            "id": "aisa/deepseek-v3.1",
            "name": "DeepSeek V3.1",
            "reasoning": true,
            "input": ["text"],
            "contextWindow": 131072,
            "maxTokens": 8192,
            "supportsDeveloperRole": false,
            "cost": { "input": 0.27, "output": 1.10, "cacheRead": 0.07 }
          },
          {
            "id": "aisa/kimi-k2.5",
            "name": "Kimi K2.5",
            "reasoning": true,
            "input": ["text"],
            "contextWindow": 131072,
            "maxTokens": 8192,
            "supportsDeveloperRole": false,
            "cost": { "input": 0.60, "output": 2.40 }
          }
        ]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "aisa/qwen3-max",
        "fallback": ["aisa/qwen-mt-flash", "aisa/deepseek-v3.1"]
      }
    }
  }
}
```

## Cost-Optimized Config (Flash for routine, Max for complex)

```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "aisa/qwen-mt-flash",
        "fallback": ["aisa/qwen-plus-2025-12-01"]
      }
    }
  }
}
```

For heavy reasoning tasks, switch model in chat:
```
/model aisa/qwen3-max
```

## Kimi K2.5 as Primary (Chinese reasoning tasks)

```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "aisa/kimi-k2.5",
        "fallback": ["aisa/qwen3-max", "aisa/deepseek-v3.1"]
      }
    }
  }
}
```

> ⚠️ Kimi K2.5 requires temperature=1.0. Other values cause API errors.

## Multi-Provider Setup (AIsa + Anthropic)

```json
{
  "models": {
    "mode": "merge",
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
            "cost": { "input": 1.20, "output": 4.80 }
          },
          {
            "id": "aisa/kimi-k2.5",
            "name": "Kimi K2.5",
            "reasoning": true,
            "input": ["text"],
            "contextWindow": 131072,
            "maxTokens": 8192,
            "supportsDeveloperRole": false,
            "cost": { "input": 0.60, "output": 2.40 }
          }
        ]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "anthropic/claude-sonnet-4-5",
        "fallback": ["aisa/qwen3-max", "aisa/kimi-k2.5"]
      }
    }
  }
}
```

## Model ID Quick Reference

| Common Name | Correct AIsa Model ID | Notes |
|-------------|----------------------|-------|
| Qwen3 Max | `aisa/qwen3-max` | Flagship, works as-is |
| Qwen Plus | `aisa/qwen-plus-2025-12-01` | ⚠️ Must use dated version |
| Qwen Flash | `aisa/qwen-mt-flash` | ⚠️ Use `qwen-mt-flash` not `qwen3-flash` |
| Qwen MT Lite | `aisa/qwen-mt-lite` | Even lighter alternative |
| DeepSeek V3.1 | `aisa/deepseek-v3.1` | Works as-is |
| DeepSeek R1 | `aisa/deepseek-r1` | Reasoning-focused variant |
| Kimi K2.5 | `aisa/kimi-k2.5` | ⚠️ Requires temperature=1.0 |
| Kimi K2 Thinking | `aisa/kimi-k2-thinking` | Extended thinking variant |
