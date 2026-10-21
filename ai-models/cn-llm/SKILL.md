---
name: cn-llm
description: 'China LLM Gateway - Unified interface for Chinese LLMs including Qwen, DeepSeek, GLM, Baichuan. OpenAI compatible, one API Key for all models. Use when: the user needs model routing, provider setup, or Chinese LLM access guidance.'
compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries curl, python3, environment variables AISA_API_KEY and internet access to api.aisa.one.
metadata:
  version: "1.0.1"
  aisa:
    emoji: 🐉
    requires:
      bins:
      - curl
      - python3
      env:
      - AISA_API_KEY
    primaryEnv: AISA_API_KEY
    compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries curl, python3, environment variables AISA_API_KEY and internet access to api.aisa.one.
---

# AIsa CN-LLM 🐉

<!-- aisa-rules:start -->
## AIsa agent rules (shared)

<!-- Generated from _shared/aisa-rules.md by scripts/sync_shared_rules.py. Do not edit this block in place. -->

These rules apply to every AIsa-backed skill and are copied from https://aisa.one/llms.txt, the single authoritative agent rule source. When this block and the rest of this skill disagree, follow this block.

### Connect (MCP first)

Pick the first option that applies. Run the command yourself; the user only approves the browser sign-in.

- **A. Your client supports remote MCP and can open a browser (default).** Add a remote MCP server named `AIsa` with URL `https://mcp.aisa.one/mcp` (Streamable HTTP), using your client's own command or config file. Auth: browser OAuth, no key needed. In a chat app (Claude, ChatGPT), the user adds it as a custom connector in settings. Adding the server does not always start sign-in. If no sign-in window opens, start it from the client's own MCP authentication entry (a menu, command, or connector button); if only the user can reach that entry, tell them where it is. Sign-in is the slow step, not the API. Before it starts, tell the user in one line that an AIsa sign-in window or card is about to open and to click **Allow** (one click if the browser is already signed in to AIsa). Do not call step 2 until the user says sign-in is done or the AIsa tools appear; calling it earlier only returns 401, so do not retry in a loop. If the client must restart to load the server, tell the user and wait. If you cannot add the connector yourself (sandbox, permission denied), give the user the server name and URL above and wait. Do not fall back to another method.
- **B. Your client supports remote MCP but has no browser (CI, SSH, container).** Same endpoint, with the header `Authorization: Bearer $AISA_API_KEY` set in your client's MCP config instead of browser sign-in. If `AISA_API_KEY` is not set, ask the user to create a key at https://console.aisa.one/api-keys and set it in the environment; never ask them to paste it into chat. Never print, log, or commit the key.
- **C. The client has no MCP support.** Use the CLI: `npm install -g @aisa-one/cli && aisa login` (Node.js 18+). Guide: https://aisa.one/docs/get-started/cli.md
- **D. Calling AIsa over HTTP from your own code.** LLMs, OpenAI-compatible: `https://api.aisa.one/v1` (Gemini GenerateContent: `https://api.aisa.one/v1beta`). Data APIs: `https://api.aisa.one/apis/v1`. Auth: `Authorization: Bearer $AISA_API_KEY`. Exact paths and schemas: https://aisa.one/docs/api-reference

Direct HTTP (D) is a gated fallback, not the default. Gate (https://aisa.one/docs/get-started/cli.md#direct-http-fallback): "CLI and MCP are both unavailable, HTTP requests are supported, and a valid existing AIsa API key is already available." The curl and script examples in this skill exist for that fallback; when a connection exists, run the same operation through MCP (`search` → `batch_get_schema` → `batch_quote` → `batch_use`) or the CLI (`aisa search` → `aisa schema` → `aisa quote` → `aisa call`). Take tool names and arguments from `search` or `batch_get_schema`. Never invent them.

### Verify (step 2)

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

**China LLM Unified Gateway. Powered by AIsa.**

One API Key to access all Chinese LLMs. OpenAI compatible interface.

Qwen, DeepSeek, GLM, Baichuan, Moonshot, and more - unified API access.

## 🔥 What You Can Do

### Intelligent Chat
```
"Use Qwen to answer Chinese questions, use DeepSeek for coding"
```

### Deep Reasoning
```
"Use DeepSeek-R1 for complex reasoning tasks"
```

### Code Generation
```
"Use DeepSeek-Coder to generate Python code with explanations"
```

### Long Text Processing
```
"Use Qwen-Long for ultra-long document summarization"
```

### Model Comparison
```
"Compare response quality between Qwen-Max and DeepSeek-V3"
```

## Supported Models

### Qwen (Alibaba)

| Model | Input Price | Output Price | Features |
|-----|---------|---------|------|
| qwen3-max | $1.37/M | $5.48/M | Most powerful general model |
| qwen3-max-2026-01-23 | $1.37/M | $5.48/M | Latest version |
| qwen3-coder-plus | $2.86/M | $28.60/M | Enhanced code generation |
| qwen3-coder-flash | $0.72/M | $3.60/M | Fast code generation |
| qwen3-coder-480b-a35b-instruct | $2.15/M | $8.60/M | 480B large model |
| qwen3-vl-plus | $0.43/M | $4.30/M | Vision-language model |
| qwen3-vl-flash | $0.86/M | $0.86/M | Fast vision model |
| qwen3-omni-flash | $4.00/M | $16.00/M | Multimodal model |
| qwen-vl-max | $0.23/M | $0.57/M | Vision-language |
| qwen-plus-2025-12-01 | $1.26/M | $12.60/M | Plus version |
| qwen-mt-flash | $0.168/M | $0.514/M | Fast machine translation |
| qwen-mt-lite | $0.13/M | $0.39/M | Lite machine translation |

### DeepSeek

| Model | Input Price | Output Price | Features |
|-----|---------|---------|------|
| deepseek-r1 | $2.00/M | $8.00/M | Reasoning model, supports Tools |
| deepseek-v3 | $1.00/M | $4.00/M | General chat, 671B parameters |
| deepseek-v3-0324 | $1.20/M | $4.80/M | V3 stable version |
| deepseek-v3.1 | $4.00/M | $12.00/M | Latest Terminus version |

> **Note**: Prices are in M (million tokens). Model availability may change, see [marketplace.aisa.one/pricing](https://marketplace.aisa.one/pricing) for the latest list.

## Quick Start

```bash
export AISA_API_KEY="your-key"
```

## API Endpoints

### OpenAI Compatible Interface

```
POST https://api.aisa.one/v1/chat/completions
```

#### Qwen Example

```bash
curl -X POST "https://api.aisa.one/v1/chat/completions" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-max",
    "messages": [
      {"role": "system", "content": "You are a professional Chinese assistant."},
      {"role": "user", "content": "Please explain what a large language model is?"}
    ],
    "temperature": 0.7,
    "max_tokens": 1000
  }'
```

#### DeepSeek Example

```bash
# DeepSeek-V3 general chat (671B parameters)
curl -X POST "https://api.aisa.one/v1/chat/completions" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-v3",
    "messages": [{"role": "user", "content": "Write a quicksort algorithm in Python"}],
    "temperature": 0.3
  }'

# DeepSeek-R1 deep reasoning (supports Tools)
curl -X POST "https://api.aisa.one/v1/chat/completions" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-r1",
    "messages": [{"role": "user", "content": "A farmer needs to cross a river with a wolf, a sheep, and a cabbage. The boat can only carry the farmer and one item at a time. If the farmer is not present, the wolf will eat the sheep, and the sheep will eat the cabbage. How can the farmer safely cross?"}]
  }'

# DeepSeek-V3.1 Terminus latest version
curl -X POST "https://api.aisa.one/v1/chat/completions" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-v3.1",
    "messages": [{"role": "user", "content": "Implement an LRU cache with get and put operations"}]
  }'
```

#### Qwen3 Code Generation Example

```bash
curl -X POST "https://api.aisa.one/v1/chat/completions" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-coder-plus",
    "messages": [{"role": "user", "content": "Implement a thread-safe Map in Go"}]
  }'
```

#### Parameter Reference

| Parameter | Type | Required | Description |
|-----|------|-----|------|
| `model` | string | Yes | Model identifier |
| `messages` | array | Yes | Message list |
| `temperature` | number | No | Randomness (0-2, default 1) |
| `max_tokens` | integer | No | Maximum tokens to generate |
| `stream` | boolean | No | Stream output (default false) |
| `top_p` | number | No | Nucleus sampling parameter (0-1) |

#### Response Format

```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "qwen-max",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "A large language model (LLM) is a deep learning-based..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 30,
    "completion_tokens": 150,
    "total_tokens": 180,
    "cost": 0.001
  }
}
```

### Streaming Output

```bash
curl -X POST "https://api.aisa.one/v1/chat/completions" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen-plus",
    "messages": [{"role": "user", "content": "Tell a Chinese folk story"}],
    "stream": true
  }'
```

Returns Server-Sent Events (SSE) format:

```
data: {"id":"chatcmpl-xxx","choices":[{"delta":{"content":"Once"}}]}
data: {"id":"chatcmpl-xxx","choices":[{"delta":{"content":" upon"}}]}
...
data: [DONE]
```

## Python Client

### CLI Usage

```bash
# Qwen chat
python3 scripts/cn_llm_client.py chat --model qwen3-max --message "Hello, please introduce yourself"

# Qwen3 code generation
python3 scripts/cn_llm_client.py chat --model qwen3-coder-plus --message "Write a binary search algorithm"

# DeepSeek-R1 reasoning
python3 scripts/cn_llm_client.py chat --model deepseek-r1 --message "Which is larger, 9.9 or 9.11? Please reason in detail"

# DeepSeek-V3 chat
python3 scripts/cn_llm_client.py chat --model deepseek-v3 --message "Tell a story" --stream

# With system prompt
python3 scripts/cn_llm_client.py chat --model qwen3-max --system "You are a classical poetry expert" --message "Write a poem about plum blossoms"

# Model comparison
python3 scripts/cn_llm_client.py compare --models "qwen3-max,deepseek-v3" --message "What is quantum computing?"

# List supported models
python3 scripts/cn_llm_client.py models
```

### Python SDK Usage

```python
from cn_llm_client import CNLLMClient

client = CNLLMClient()  # Uses AISA_API_KEY environment variable

# Qwen chat
response = client.chat(
    model="qwen3-max",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response["choices"][0]["message"]["content"])

# Qwen3 code generation
response = client.chat(
    model="qwen3-coder-plus",
    messages=[
        {"role": "system", "content": "You are a professional programmer."},
        {"role": "user", "content": "Implement a singleton pattern in Python"}
    ],
    temperature=0.3
)

# Streaming output
for chunk in client.chat_stream(
    model="deepseek-v3",
    messages=[{"role": "user", "content": "Tell a story about an idiom"}]
):
    print(chunk, end="", flush=True)

# Model comparison
results = client.compare_models(
    models=["qwen3-max", "deepseek-v3", "deepseek-r1"],
    message="Explain what machine learning is"
)
for model, result in results.items():
    print(f"{model}: {result['response'][:100]}...")
```

## Use Cases

### 1. Chinese Content Generation

```python
# Copywriting
response = client.chat(
    model="qwen3-max",
    messages=[
        {"role": "system", "content": "You are a professional copywriter."},
        {"role": "user", "content": "Write a product introduction for a smart watch"}
    ]
)
```

### 2. Code Development

```python
# Code generation and explanation
response = client.chat(
    model="qwen3-coder-plus",
    messages=[{"role": "user", "content": "Implement a thread-safe Map in Go"}]
)
```

### 3. Complex Reasoning

```python
# Mathematical reasoning
response = client.chat(
    model="deepseek-r1",
    messages=[{"role": "user", "content": "Prove: For any positive integer n, n³-n is divisible by 6"}]
)
```

### 4. Visual Understanding

```python
# Image understanding
response = client.chat(
    model="qwen3-vl-plus",
    messages=[
        {"role": "user", "content": [
            {"type": "text", "text": "Describe the content of this image"},
            {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
        ]}
    ]
)
```

### 5. Model Routing Strategy

```python
MODEL_MAP = {
    "chat": "qwen3-max",           # General chat
    "code": "qwen3-coder-plus",    # Code generation
    "reasoning": "deepseek-r1",    # Complex reasoning
    "vision": "qwen3-vl-plus",     # Visual understanding
    "fast": "qwen3-coder-flash",   # Fast response
    "translate": "qwen-mt-flash"   # Machine translation
}

def route_by_task(task_type: str, message: str) -> str:
    model = MODEL_MAP.get(task_type, "qwen3-max")
    return client.chat(model=model, messages=[{"role": "user", "content": message}])
```

## Error Handling

Errors return JSON with `error` field:

```json
{
  "error": {
    "code": "model_not_found",
    "message": "Model 'xxx' is not available"
  }
}
```

Common error codes:
- `401` - Invalid or missing API Key
- `402` - Insufficient balance
- `404` - Model not found
- `429` - Rate limit exceeded
- `500` - Server error

## Pricing

| Model | Input ($/M) | Output ($/M) |
|-----|-----------|-----------|
| qwen3-max | $1.37 | $5.48 |
| qwen3-coder-plus | $2.86 | $28.60 |
| qwen3-coder-flash | $0.72 | $3.60 |
| qwen3-vl-plus | $0.43 | $4.30 |
| deepseek-v3 | $1.00 | $4.00 |
| deepseek-r1 | $2.00 | $8.00 |
| deepseek-v3.1 | $4.00 | $12.00 |

> Price unit: $ per Million tokens. The settled cost of each call is returned in the `X-AISA-Customer-Cost-Micros-USD` response header (integer micro-USD; 1 USD = 1,000,000). Do not look for a cost field in the response body.

## Get Started

1. Register at [aisa.one](https://aisa.one)
2. Get API Key
3. Top up (pay-as-you-go)
4. Set environment variable: `export AISA_API_KEY="your-key"`

## Full API Reference

See [API Reference](https://docs.aisa.one/reference/) for complete endpoint documentation.
