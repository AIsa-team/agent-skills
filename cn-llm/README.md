# AIsa CN-LLM 🐉

**China LLM Unified Gateway. Powered by AIsa.**

One API Key to access Qwen3 and DeepSeek series models.

## Quick Start

```bash
# Set API Key
export AISA_API_KEY="your-key"

# Qwen chat
python3 scripts/cn_llm_client.py chat --model qwen3-max --message "Hello"

# Qwen3 code generation
python3 scripts/cn_llm_client.py chat --model qwen3-coder-plus --message "Write a quicksort"

# DeepSeek-R1 reasoning
python3 scripts/cn_llm_client.py chat --model deepseek-r1 --message "Which is larger, 9.9 or 9.11?"

# DeepSeek-V3 chat
python3 scripts/cn_llm_client.py chat --model deepseek-v3 --message "Tell a story" --stream

# Model comparison
python3 scripts/cn_llm_client.py compare --models "qwen3-max,deepseek-v3" --message "What is AI"

# List models
python3 scripts/cn_llm_client.py models
```

## Supported Models

| Model Series | Available Models |
|---------|----------|
| Qwen3 General | qwen3-max, qwen3-max-2026-01-23 |
| Qwen3 Code | qwen3-coder-plus, qwen3-coder-flash, qwen3-coder-480b-a35b-instruct |
| Qwen3 Vision | qwen3-vl-plus, qwen3-vl-flash, qwen3-omni-flash |
| Qwen Other | qwen-vl-max, qwen-mt-flash, qwen-mt-lite |
| DeepSeek | deepseek-r1, deepseek-v3, deepseek-v3-0324, deepseek-v3.1 |

## OpenAI SDK Compatible

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["AISA_API_KEY"],
    base_url="https://api.aisa.one/v1"
)

response = client.chat.completions.create(
    model="qwen3-max",  # or deepseek-v3, deepseek-r1, etc.
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

See [SKILL.md](SKILL.md) for detailed documentation.
