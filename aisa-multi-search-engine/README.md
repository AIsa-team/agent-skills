# AIsa Multi Search Engine

Multi-source search engine plugin for [OpenClaw](https://docs.openclaw.ai), powered by [AIsa API](https://aisa.one).

One API key. Seven search tools. Web, academic, Tavily, and Perplexity — unified with confidence scoring.

## Install

```bash
openclaw plugins install aisa-multi-search-engine
```

## Configure

Set your AIsa API key:

```bash
export AISA_API_KEY="your-key-here"
```

Or configure in OpenClaw plugin settings:

```json
{
  "plugins": {
    "entries": {
      "aisa-multi-search-engine": {
        "config": {
          "aisaApiKey": "your-key-here"
        }
      }
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `aisa_web_search` | Structured web search |
| `aisa_scholar_search` | Academic paper search with year filtering |
| `aisa_smart_search` | Hybrid web + academic search |
| `aisa_tavily_search` | Advanced search with depth, topic, time, domain filters |
| `aisa_tavily_extract` | Extract content from URLs |
| `aisa_perplexity_search` | Deep research via Perplexity Sonar models |
| `aisa_multi_search` | Parallel multi-source search with confidence scoring |

## License

MIT
