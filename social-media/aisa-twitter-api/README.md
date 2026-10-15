# AIsa Twitter API

Search and inspect X posts, profiles, timelines, communities, and trends through
AIsa. Publish authorized text or media posts using an OAuth-linked X account.
Requires Python 3.11+, POSIX, and an AIsa API key; runtime uses the standard library.

```bash
# Free quote without retrieving data
python3 scripts/twitter_client.py search --query "AI agents" --quote

# Offline preview without credentials or publishing
python3 scripts/twitter_oauth_client.py post --text "Shipping today." --dry-run

# Run offline tests
python3 -m unittest discover -s tests -v
```

Executed requests require an approved budget and durable ledger. Quotes are
estimates, not guaranteed final costs; unknown charges block further requests.
Provider data remains intact with `_aisa` HTTP/billing metadata. Commands fetch a
single page and do not schedule monitoring.

See [SKILL.md](SKILL.md) for research and authorization,
[posting and media](references/post_twitter.md) for publishing, and
[cost controls](references/cost-control.md) for budgets and recovery.

## API reference

See the [AIsa API Reference](https://aisa.one/docs/api-reference) for current
operation contracts. The suite's contract snapshot supports offline validation;
production retrieval and posting require separately authorized live tests.
