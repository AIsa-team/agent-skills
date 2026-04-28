# AIsa Search Command Center

Flagship AIsa search lane for live lookup, source discovery, cited answers, and deep research.

## Features

- Web search
- Scholar search
- Hybrid scholar search
- Perplexity Sonar, Sonar Pro, Sonar Reasoning Pro, and Sonar Deep Research
- Tavily integration
- Verity-style multi-source retrieval

## Best For

- Fast live search when the user wants one broad search entry point
- Citation-ready answers without switching skills
- Deep research reports that may expand from short lookup to wider synthesis

## Quick Start

```bash
export AISA_API_KEY="your-key"

python scripts/search_client.py web --query "AI frameworks"
python scripts/search_client.py scholar --query "transformer models"
python scripts/search_client.py sonar --query "What changed in AI this week?"
python scripts/search_client.py sonar-pro --query "Compare coding agents with citations"
python scripts/search_client.py verity --query "Is quantum computing enterprise-ready?"
```

## Notes

- Deprecated `/search/full` and `/search/smart` nodes were removed from this skill.
- Perplexity endpoints are now the recommended answer-generation path.

## Documentation

See [SKILL.md](SKILL.md) for full usage and examples.
