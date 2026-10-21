# Changelog

## 1.0.0

- Integrate the shared MCP-first connection and spending rules. Validate provider image dimensions before reserving an attempt, recover successful synchronous responses after a cache-write failure without resubmitting, and retain allowlisted request IDs and settled-cost headers with unknown costs explicitly distinguished.

- 2026-10-21: Add a catalog-gated GPT Image 2 JSON edit adapter with inline references, PNG output, medium quality and bounded native sizes; prohibit automatic model fallback. Verify one live `gpt-image-2` 1024×1024 request through the direct source adapter; record product-detail drift and distinguish this from the full CLI workflow or WorkBuddy MCP execution. Document the current Gemini catalog gap. Keep the skill version at 1.0.0.
- Add a concise menu as the first response on every new invocation, in the user’s language; honor existing choices and preserve photo and approval gates.


Documented: 2026-10-18.

- Introduce `e-commerce-content-studio` as the product-content successor to Python `media-gen`; the name, runtime and workflow are breaking changes.
- Move executable implementation to TypeScript with compiled JavaScript distribution.
- Require usable user-supplied product photos per SKU before research, including copy-only requests.
- Separate current platform research, comparable-creative evidence, a versioned playbook and explicit user approval from production.
- Define initial content workflows for Amazon US, TikTok Shop US product listings and Shopify product pages; distinguish these profiles from native platform integrations and future support.
- Require product-fidelity inspection, truthful claims, saved artifacts and technical validation before delivery; keep publishing outside the workflow.
- Document performance evidence tiers, source freshness, policy conflicts and staged platform expansion without promising unimplemented support or verified live generation.
- Scope production to local photo exports, catalog-gated GPT Image or Gemini inline-reference edits and chat copy; expose Wan 2.7 image-to-video only as an explicitly approved experimental route requiring a matching user-hosted HTTPS photo.
- Document unsupported background removal, other image-edit adapters, media uploads, video assembly and captions; distinguish estimate/attempt controls from a provider billing cap.
