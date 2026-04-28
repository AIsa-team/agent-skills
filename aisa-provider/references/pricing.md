# AIsa Pricing Reference

> ⚠️ All prices below are for reference only (as of February 2026). Real-time pricing is subject to change — always check https://marketplace.aisa.one/pricing for the latest rates.

All prices are per 1 million tokens (USD).

## Text Models

### Qwen MT Flash (lightweight, high-frequency)

| Metric | AIsa | Bailian Official | OpenRouter | Savings |
|--------|------|------------------|------------|---------|
| Input/1M | $0.05 | $0.10 | $0.11-0.13 | ~50% off |
| Output/1M | $0.30 | $0.40 | $0.45-0.50 | ~25% off |

### Qwen Plus (main production model)

| Metric | AIsa | Bailian Official | OpenRouter | Savings |
|--------|------|------------------|------------|---------|
| Input/1M | $0.30 | $0.40 | $0.45-0.50 | ~25% off |
| Output/1M | $0.90 | $1.20 | $1.35-1.50 | ~25% off |
| Thinking Output/1M | $3.00 | $4.00 | $4.50-5.00 | ~25% off |

### Qwen3 Max (flagship, complex reasoning)

| Metric | AIsa | Bailian Official | OpenRouter | Savings |
|--------|------|------------------|------------|---------|
| Input/1M | $1.20 | $2.00 | $2.20-2.50 | ~40% off |
| Output/1M | $4.80 | $8.00 | $9.00-10.00 | ~40% off |

### ⭐ Kimi K2.5 (Moonshot AI flagship)

AIsa provides Kimi K2.5 at approximately **80% of official Moonshot pricing** (~20% discount).

| Metric | AIsa | Moonshot Official | Savings |
|--------|------|-------------------|---------|
| Input/1M | ~$0.60 | ~$0.75 | ~20% off |
| Output/1M | ~$2.40 | ~$3.00 | ~20% off |

**Notes on Kimi K2.5:**
- 🔒 **Zero Data Retention (ZDR)**: AIsa has a formal enterprise ZDR agreement with Moonshot (dated Feb 10, 2026) — customer data and outputs are not retained or used for training
- Pricing is approximate and subject to Moonshot's rate changes
- Kimi K2.5 is not widely available on other aggregation platforms (limited availability on OpenRouter)
- AIsa's access is through direct Moonshot partnership
- Requires `temperature=1.0` — other values cause API errors

### DeepSeek V3.1

| Metric | AIsa |
|--------|------|
| Input/1M | $0.27 |
| Output/1M | $1.10 |
| Cache Read/1M | $0.07 |

## Image & Video Models (exclusive to AIsa, not available on OpenRouter)

| Model | AIsa | Bailian Official |
|-------|------|------------------|
| Qwen-VL / WAN image | $0.02-0.03/image | $0.04/image |
| WAN 720P video | $0.08/sec | $0.10/sec |
| WAN 1080P video | $0.12/sec | $0.15/sec |

## Scale Cost Comparison (500M tokens/month, Qwen-Max)

| Provider | Monthly Cost | Annual Cost |
|----------|-------------|-------------|
| OpenRouter | $4,000-4,250 | $48,000-51,000 |
| Bailian Official | $3,400 | $40,800 |
| **AIsa** | **$2,040** | **$24,480** |
| **Annual savings vs OpenRouter** | | **$23,520-26,520** |
| **Annual savings vs Bailian** | | **$16,320** |

## Provider Comparison

| Feature | AIsa | Qwen Portal (free) | OpenRouter |
|---------|------|---------------------|------------|
| Partnerships | Official (all major Chinese AI) | OAuth free tier | Router (adds markup) |
| Pricing | Up to 50% off retail | Free tier | +10-25% markup |
| Model coverage | Qwen (all) + Doubao + DeepSeek + Kimi K2.5 | 2 Qwen models | Limited Chinese models |
| Kimi K2.5 | ✅ ~80% of official price | ❌ | Limited |
| Kimi K2.5 ZDR | ✅ Enterprise ZDR agreement | ❌ | ❌ |
| Latest models | WAN 2.6 multimodal (20% off) | Not available | Not available |
| Qwen regions | CN, US (Virginia), SG | CN only | Global |
| Daily limits | None | 2,000 req/day | None |
| Best for | Production | Testing/prototyping | Convenience |

## Savings Summary by Model

| Model | AIsa vs Official | AIsa vs OpenRouter |
|-------|------------------|--------------------|
| Qwen MT Flash | ~50% cheaper | ~55-60% cheaper |
| Qwen Plus | ~25% cheaper | ~35-40% cheaper |
| Qwen3 Max | ~40% cheaper | ~45-50% cheaper |
| Kimi K2.5 | ~20% cheaper | N/A (limited on OR) |
| DeepSeek V3.1 | Competitive | Competitive |
