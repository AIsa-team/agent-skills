# Changelog

## 1.1.0

- Match current community-search parameters, OAuth response shapes, reply/quote fields, and dedicated media upload followed by media-ID posting.
- Remove API keys from command output, reject authenticated redirects, retain billing headers on response failures, and return nonzero for HTTP/provider/decoding errors.
- Require explicit execution budgets with exact micro-USD ledgers, verified free quotes, unknown-charge blocking, and no automatic request retries. Final charges can exceed admission estimates.
- Add offline posting previews and explicit thread expansion with reply continuations; preserve partial upload/post results and stop on ambiguous outcomes.
- Keep credential resolution compatible, document unsupported Spaces cost controls and conflicting pagination contracts, and add standalone regression tests.

## 1.0.5

- Establish the independently versioned baseline and maintenance manifest.
- Preserve the existing skill contract and declare tracked upstream sources.
