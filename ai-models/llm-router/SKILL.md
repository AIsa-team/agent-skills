---
name: llm-router
description: 'Unified LLM Gateway - One API for 70+ AI models. Route to GPT, Claude, Gemini, Qwen, Deepseek, Grok and more with a single API key. Use when: the user needs model routing, provider setup, or Chinese LLM access guidance.'
compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries curl, python3, environment variables AISA_API_KEY and internet access to api.aisa.one.
metadata:
  version: "1.0.1"
  aisa:
    emoji: 🧠
    requires:
      bins:
      - curl
      - python3
      env:
      - AISA_API_KEY
    primaryEnv: AISA_API_KEY
    compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries curl, python3, environment variables AISA_API_KEY and internet access to api.aisa.one.
---

# AIsa LLM Router 🧠

<!-- aisa-rules:start -->
## AIsa agent rules (shared)

<!-- Generated from _shared/aisa-rules.md by scripts/sync_shared_rules.py. Do not edit this block in place. -->

These rules apply to every AIsa-backed skill and are copied from https://aisa.one/llms.txt, the single authoritative agent rule source. When this block and the rest of this skill disagree, follow this block.

### Connect (MCP first)

Pick the first option that applies. Run the command yourself; the user only approves the browser sign-in.

- **A. Your client supports remote MCP and can open a browser (default).** Add a remote MCP server named `AIsa` with URL `https://mcp.aisa.one/mcp` (Streamable HTTP), using your client's own command or config file. Auth: browser OAuth, no key needed. In a chat app (Claude, ChatGPT), the user adds it as a custom connector in settings. If you cannot add the connector yourself (sandbox, permission denied), give the user the server name and URL above and wait. Do not fall back to another method.
- **B. Your client supports remote MCP but has no browser (CI, SSH, container).** Same endpoint, with the header `Authorization: Bearer $AISA_API_KEY` set in your client's MCP config instead of browser sign-in. If `AISA_API_KEY` is not set, ask the user to create a key at https://console.aisa.one/api-keys and set it in the environment; never ask them to paste it into chat. Never print, log, or commit the key.
- **C. The client has no MCP support.** Use the CLI: `npm install -g @aisa-one/cli && aisa login` (Node.js 18+). Guide: https://aisa.one/docs/get-started/cli.md
- **D. Calling AIsa over HTTP from your own code.** LLMs, OpenAI-compatible: `https://api.aisa.one/v1` (Gemini GenerateContent: `https://api.aisa.one/v1beta`). Data APIs: `https://api.aisa.one/apis/v1`. Auth: `Authorization: Bearer $AISA_API_KEY`. Exact paths and schemas: https://aisa.one/docs/api-reference

Direct HTTP (D) is a gated fallback, not the default. Gate (https://aisa.one/docs/get-started/cli.md#direct-http-fallback): "CLI and MCP are both unavailable, HTTP requests are supported, and a valid existing AIsa API key is already available." The curl and script examples in this skill exist for that fallback; when a connection exists, run the same operation through MCP (`search` → `batch_get_schema` → `batch_quote` → `batch_use`) or the CLI (`aisa search` → `aisa schema` → `aisa quote` → `aisa call`). Take tool names and arguments from `search` or `batch_get_schema`. Never invent them.

### Verify

Make one free authenticated call on the interface you connected:

- MCP (A, B): call `account` (no arguments). If it is not in the tool list, call `use` with `{"operation_id": "account"}` instead. Returns the key, balance, and usage.
- CLI (C): `aisa balance`. (`aisa whoami` is local only and does not count.)
- HTTP (D): `GET https://api.aisa.one/v1/models` with the Bearer header returns 200.

AIsa is connected only when this call succeeds. A tool list or a 401 response does not count.

### Spending (approval before paid calls)

- Free: docs, `GET /v1/models`, MCP `search`, `list_categories`, `batch_get_schema`, `batch_quote`, `account`, and CLI `aisa search`, `aisa schema`, `aisa quote`, `aisa balance`.
- Quote the exact calls before running them: MCP `batch_quote`, CLI `aisa quote --json`. Run only what you quoted; re-quote if the tools or arguments change. Neither `batch_use` nor `aisa call` takes a price cap.
- If the quote reports `auto_execute_eligible: true` (a small total), run it without asking, unless the user set a tighter limit or asked only for a quote.
- Otherwise, before the first such call, tell the user in one message what you plan to call, the quoted price, and a total budget for the task in USD. Wait for approval, then run calls within that budget without asking again. Ask again only if the task changes or the next call would exceed the remaining budget.
- For operations billed by rows or credits, also set the operation's own limit (for example `limit`) so the cost stays bounded.
- Do not retry a failed paid call without telling the user.
- Direct HTTP (D) follows the stricter rule at https://aisa.one/docs/get-started/cli.md#direct-http-fallback: read the endpoint's reference and published pricing first; state the exact endpoint and scope, formula or rate, and documented maximum USD exposure; then wait for a separate user message explicitly approving that scope and cap. Do not make paid calls to test availability. Docs, `/v1/models`, and capability or MCP discovery are allowed before approval.

### Cost accounting

The settled cost of a direct HTTP call is reported by the response header `X-AISA-Customer-Cost-Micros-USD` (integer micro-USD; 1 USD = 1,000,000 micro-USD), or by a successful native Tool result's `customer_cost_micros_usd`. Missing cost metadata means unknown, not free. Response bodies do not carry `usage.cost` or `usage.credits_remaining`; do not report those fields as the charge. Reference: https://aisa.one/docs/guides/pricing

### Errors

- `401`: not signed in or invalid key. Redo Connect option A (step 1A in llms.txt) or check the key.
- `402`: low balance, or the operation requires the Go-to-Market plan. The response says which and where to resolve it. Tell the user which one it is (top up the balance, or subscribe to the plan) with the link from the response; do not retry.
- `429`: rate limited. Wait and retry with backoff. Details: https://aisa.one/docs/api-reference/rate-limits
<!-- aisa-rules:end -->

**Unified LLM Gateway for autonomous agents. Powered by AIsa.**

One API key. 70+ models. OpenAI-compatible.

Replace 100+ API keys with one. Access GPT-4, Claude-3, Gemini, Qwen, Deepseek, Grok, and more through a unified, OpenAI-compatible API.

## 🔥 What Can You Do?

### Multi-Model Chat
```
"Chat with GPT-4 for reasoning, switch to Claude for creative writing"
```

### Model Comparison
```
"Compare responses from GPT-4, Claude, and Gemini for the same question"
```

### Vision Analysis
```
"Analyze this image with GPT-4o - what objects are in it?"
```

### Cost Optimization
```
"Route simple queries to fast/cheap models, complex queries to GPT-4"
```

### Fallback Strategy
```
"If GPT-4 fails, automatically try Claude, then Gemini"
```

## Why LLM Router?

| Feature | LLM Router | Direct APIs |
|---------|------------|-------------|
| API Keys | 1 | 10+ |
| SDK Compatibility | OpenAI SDK | Multiple SDKs |
| Billing | Unified | Per-provider |
| Model Switching | Change string | Code rewrite |
| Fallback Routing | Built-in | DIY |
| Cost Tracking | Unified | Fragmented |

## Supported Model Families

| Family | Developer | Example Models |
|--------|-----------|----------------|
| GPT | OpenAI | gpt-4.1, gpt-4o, gpt-4o-mini, o1, o1-mini, o3-mini |
| Claude | Anthropic | claude-3-5-sonnet, claude-3-opus, claude-3-sonnet |
| Gemini | Google | gemini-2.0-flash, gemini-1.5-pro, gemini-1.5-flash |
| Qwen | Alibaba | qwen-max, qwen-plus, qwen2.5-72b-instruct |
| Deepseek | Deepseek | deepseek-chat, deepseek-coder, deepseek-v3, deepseek-r1 |
| Grok | xAI | grok-2, grok-beta |

> **Note**: Model availability may vary. Check [marketplace.aisa.one/pricing](https://marketplace.aisa.one/pricing) for the full list of currently available models and pricing.

## Quick Start

```bash
export AISA_API_KEY="your-key"
```

## API Endpoints

### OpenAI-Compatible Chat Completions

```
POST https://api.aisa.one/v1/chat/completions
```

#### Request

```bash
curl -X POST "https://api.aisa.one/v1/chat/completions" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4.1",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Explain quantum computing in simple terms."}
    ],
    "temperature": 0.7,
    "max_tokens": 1000
  }'
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string | Yes | Model identifier (e.g., `gpt-4.1`, `claude-3-sonnet`) |
| `messages` | array | Yes | Conversation messages |
| `temperature` | number | No | Randomness (0-2, default: 1) |
| `max_tokens` | integer | No | Maximum response tokens |
| `stream` | boolean | No | Enable streaming (default: false) |
| `top_p` | number | No | Nucleus sampling (0-1) |
| `frequency_penalty` | number | No | Frequency penalty (-2 to 2) |
| `presence_penalty` | number | No | Presence penalty (-2 to 2) |
| `stop` | string/array | No | Stop sequences |

#### Message Format

```json
{
  "role": "user|assistant|system",
  "content": "message text or array for multimodal"
}
```

#### Response

```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "gpt-4.1",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Quantum computing uses..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 50,
    "completion_tokens": 200,
    "total_tokens": 250,
    "cost": 0.0025
  }
}
```

### Streaming Response

```bash
curl -X POST "https://api.aisa.one/v1/chat/completions" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-sonnet",
    "messages": [{"role": "user", "content": "Write a poem about AI."}],
    "stream": true
  }'
```

Streaming returns Server-Sent Events (SSE):

```
data: {"id":"chatcmpl-xxx","choices":[{"delta":{"content":"In"}}]}
data: {"id":"chatcmpl-xxx","choices":[{"delta":{"content":" circuits"}}]}
...
data: [DONE]
```

### Vision / Image Analysis

Analyze images by passing image URLs or base64 data:

```bash
curl -X POST "https://api.aisa.one/v1/chat/completions" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "messages": [
      {
        "role": "user",
        "content": [
          {"type": "text", "text": "What is in this image?"},
          {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
        ]
      }
    ]
  }'
```

### Function Calling

Enable tools/functions for structured outputs:

```bash
curl -X POST "https://api.aisa.one/v1/chat/completions" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4.1",
    "messages": [{"role": "user", "content": "What is the weather in Tokyo?"}],
    "functions": [
      {
        "name": "get_weather",
        "description": "Get current weather for a location",
        "parameters": {
          "type": "object",
          "properties": {
            "location": {"type": "string", "description": "City name"},
            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
          },
          "required": ["location"]
        }
      }
    ],
    "function_call": "auto"
  }'
```

### Google Gemini Format

For Gemini models, you can also use the native format:

```
POST https://api.aisa.one/v1/models/{model}:generateContent
```

```bash
curl -X POST "https://api.aisa.one/v1/models/gemini-2.0-flash:generateContent" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [
      {
        "role": "user",
        "parts": [{"text": "Explain machine learning."}]
      }
    ],
    "generationConfig": {
      "temperature": 0.7,
      "maxOutputTokens": 1000
    }
  }'
```

## Python Client

### Installation

No installation required - uses standard library only.

### CLI Usage

```bash
# Basic completion
python3 scripts/llm_router_client.py chat --model gpt-4.1 --message "Hello, world!"

# With system prompt
python3 scripts/llm_router_client.py chat --model claude-3-sonnet --system "You are a poet" --message "Write about the moon"

# Streaming
python3 scripts/llm_router_client.py chat --model gpt-4o --message "Tell me a story" --stream

# Multi-turn conversation
python3 scripts/llm_router_client.py chat --model qwen-max --messages '[{"role":"user","content":"Hi"},{"role":"assistant","content":"Hello!"},{"role":"user","content":"How are you?"}]'

# Vision analysis
python3 scripts/llm_router_client.py vision --model gpt-4o --image "https://example.com/image.jpg" --prompt "Describe this image"

# List supported models
python3 scripts/llm_router_client.py models

# Compare models
python3 scripts/llm_router_client.py compare --models "gpt-4.1,claude-3-sonnet,gemini-2.0-flash" --message "What is 2+2?"
```

### Python SDK Usage

```python
from llm_router_client import LLMRouterClient

client = LLMRouterClient()  # Uses AISA_API_KEY env var

# Simple chat
response = client.chat(
    model="gpt-4.1",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response["choices"][0]["message"]["content"])

# With options
response = client.chat(
    model="claude-3-sonnet",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain relativity."}
    ],
    temperature=0.7,
    max_tokens=500
)

# Streaming
for chunk in client.chat_stream(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Write a story."}]
):
    print(chunk, end="", flush=True)

# Vision
response = client.vision(
    model="gpt-4o",
    image_url="https://example.com/image.jpg",
    prompt="What's in this image?"
)

# Compare models
results = client.compare_models(
    models=["gpt-4.1", "claude-3-sonnet", "gemini-2.0-flash"],
    message="Explain quantum computing"
)
for model, result in results.items():
    print(f"{model}: {result['response'][:100]}...")
```

## Use Cases

### 1. Cost-Optimized Routing

Use cheaper models for simple tasks:

```python
def smart_route(message: str) -> str:
    # Simple queries -> fast/cheap model
    if len(message) < 50:
        model = "gpt-3.5-turbo"
    # Complex reasoning -> powerful model
    else:
        model = "gpt-4.1"
    
    return client.chat(model=model, messages=[{"role": "user", "content": message}])
```

### 2. Fallback Strategy

Automatic fallback on failure:

```python
def chat_with_fallback(message: str) -> str:
    models = ["gpt-4.1", "claude-3-sonnet", "gemini-2.0-flash"]
    
    for model in models:
        try:
            return client.chat(model=model, messages=[{"role": "user", "content": message}])
        except Exception:
            continue
    
    raise Exception("All models failed")
```

### 3. Model A/B Testing

Compare model outputs:

```python
results = client.compare_models(
    models=["gpt-4.1", "claude-3-opus"],
    message="Analyze this quarterly report..."
)

# Log for analysis
for model, result in results.items():
    log_response(model=model, latency=result["latency"], cost=result["cost"])
```

### 4. Specialized Model Selection

Choose the best model for each task:

```python
MODEL_MAP = {
    "code": "deepseek-coder",
    "creative": "claude-3-opus",
    "fast": "gpt-3.5-turbo",
    "vision": "gpt-4o",
    "chinese": "qwen-max",
    "reasoning": "gpt-4.1"
}

def route_by_task(task_type: str, message: str) -> str:
    model = MODEL_MAP.get(task_type, "gpt-4.1")
    return client.chat(model=model, messages=[{"role": "user", "content": message}])
```

## Error Handling

Errors return JSON with `error` field:

```json
{
  "error": {
    "code": "model_not_found",
    "message": "Model 'xyz' is not available"
  }
}
```

Common error codes:
- `401` - Invalid or missing API key
- `402` - Insufficient credits
- `404` - Model not found
- `429` - Rate limit exceeded
- `500` - Server error

## Best Practices

1. **Use streaming** for long responses to improve UX
2. **Set max_tokens** to control costs
3. **Implement fallback** for production reliability
4. **Cache responses** for repeated queries
5. **Monitor usage** via response metadata
6. **Use appropriate models** - don't use GPT-4 for simple tasks

## OpenAI SDK Compatibility

Just change the base URL and key:

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["AISA_API_KEY"],
    base_url="https://api.aisa.one/v1"
)

response = client.chat.completions.create(
    model="gpt-4.1",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

## Pricing

Token-based pricing varies by model. Check [marketplace.aisa.one/pricing](https://marketplace.aisa.one/pricing) for current rates.

| Model Family | Approximate Cost |
|--------------|------------------|
| GPT-4.1 / GPT-4o | ~$0.01 / 1K tokens |
| Claude-3-Sonnet | ~$0.01 / 1K tokens |
| Gemini-2.0-Flash | ~$0.001 / 1K tokens |
| Qwen-Max | ~$0.005 / 1K tokens |
| DeepSeek-V3 | ~$0.002 / 1K tokens |

Every response includes `usage.cost` and `usage.credits_remaining`.

## Get Started

1. Sign up at [aisa.one](https://aisa.one)
2. Get your API key from the dashboard
3. Add credits (pay-as-you-go)
4. Set environment variable: `export AISA_API_KEY="your-key"`

## Full API Reference

See [API Reference](https://aisa.mintlify.app/api-reference/introduction) for complete endpoint documentation.
