# Platform scope, requirement research and evidence

## Supported workflow profiles

Version 1.0.0 supports the following profiles. A profile helps plan and validate an export; it is not an account connector, uploader or substitute for current policy research.

**All video production remains experimental.** The profiles below describe target placements, while the only implemented video adapter is Wan 2.7 image-to-video with a matching user-hosted public HTTPS product photo. Its gateway behavior and output quality have not been verified by authenticated end-to-end generation. Explicit `allowExperimentalVideo: true` and user approval of the disclosed limitation are required. The runtime does not assemble clips, add captions or upload reference photos; see [aisa-contract.md](aisa-contract.md).

| Platform | Market | Profile | Output context |
| --- | --- | --- | --- |
| Amazon | US | `amazon-main` | Main product image for a listing/search result |
| Amazon | US | `amazon-gallery` | Additional listing images: details, supported use cases and relevant information |
| Amazon | US | `amazon-copy` | Listing fields appropriate to the current product type, such as title, highlights, bullets and description |
| Amazon | US | `amazon-video` | Product listing video; verify current placement and account eligibility |
| TikTok Shop | US | `tiktok-gallery` | Product listing images |
| TikTok Shop | US | `tiktok-copy` | Product listing title, description and required attributes |
| TikTok Shop | US | `tiktok-video` | Product listing video |
| Shopify | Explicit destination country | `shopify-gallery` | Product-page gallery fitted to the actual theme/layout |
| Shopify | Explicit destination country | `shopify-copy` | Product-page text and requested search metadata |
| Shopify | Explicit destination country | `shopify-video` | Product-page video supported by the selected theme |

Require a destination language for every profile. Product category, SKU/variant and placement are part of the requirement key. Shopify support does not mean that every category, jurisdiction or third-party sales channel has a maintained policy pack: research destination rules and report unresolved requirements for the actual request.

For images, `local-photo-export` fits/resizes the supplied photo without removing its background or creating unseen angles. It is the only mode accepted for `amazon-main` in 1.0.0; provide an already compliant source photograph and verify final framing. Gemini reference editing is the only implemented generative image-edit route for other image profiles; other models advertised by a catalog are not automatically usable by this skill.

Excluded in 1.0.0: Amazon A+ modules and paid-ad placements; TikTok paid ads, organic campaigns and LIVE; Shopify marketplace feeds, campaign placements and store implementation; native seller-account analytics and automatic publishing. A generic image or video adapter does not extend the supported platform scope.

## Freshness and precedence

Reopen applicable official sources during **each run**, after the product-photo gate. These links were selected during development on 18 October 2026; that date is not verification for a later job. Search for replacements if an official page moves. Record inaccessible pages as gaps, not confirmed rules.

For each material requirement, save:

- Platform, market, category/product type, placement and language.
- Source title and canonical URL; retrieval date/time; publication/effective date when available.
- The actual relevant requirement, its scope and whether it is mandatory, a quality recommendation or an experimental hypothesis.
- The corresponding output check and evidence needed to evaluate it.
- Conflicts, exceptions, inaccessible evidence and the reason for the chosen interpretation.

Prefer the applicable current policy and category specification over a general help article, an old announcement or a marketing recommendation. Check the actual seller form when the user provides legitimate access and a decisive field limit remains unclear. Do not bypass access controls. If two authoritative applicable sources still conflict, flag the issue and withhold affected production/export claims until resolved; adopting a conservative common constraint is acceptable only when it actually satisfies both sources and the user understands the limitation.

Separate technical acceptance, content policy, recommended creative practice and commercial effectiveness. Passing a file validator does not prove compliance with every rule or effectiveness. User approval cannot make a platform-prohibited claim acceptable.

## Amazon US official sources

- [Product image guide](https://sellercentral.amazon.com/help/hub/reference/external/G1881?ld=a): main versus other image variants, category-specific exceptions, technical requirements and AI-generated-person disclosure metadata.
- [Product detail page rules](https://sellercentral.amazon.com/gp/help/external/G200390640?locale=en-US): prohibited listing content and field rules. Follow the current product-title requirements linked there.
- [Title policy change announced in June 2026](https://sellercentral.amazon.com/seller-forums/discussions/t/2f40628c-eb97-4b24-b983-cb1e331e06dc): a historical change example, not a perpetual source of current limits. It introduced shorter titles and a separate Item Highlights field; recheck the active policy.
- [Shoppable video guide](https://sellercentral.amazon.com/help/hub/reference/external/Y4LL3M3WJEFE8MZ?locale=en-US): product-video specifications, eligibility and placement conditions. Do not substitute Amazon Ads specifications.
- [Manage Your Experiments](https://sell.amazon.com/tools/manage-your-experiments): eligible sellers can test listing content; use actual user-provided results when available. This skill does not connect this service.
- [Best Sellers Rank explanation](https://sell.amazon.com/blog/amazon-best-sellers-rank): rank is a product-sales signal, not causal evidence for a particular image or title.

Research category style guides from the active policy pages. Main-image rules and gallery-image rules are different. Validate counts, included accessories and variant colors against the SKU, and verify required disclosure metadata when synthetic people are used. Preserve the product's actual branding; do not generate imitation platform badges or endorsements.

## TikTok Shop US official sources

- [Product Listing Policy](https://seller-us.tiktok.com/university/course?content_id=7073362639816491&learning_id=7350062255294222): US listing scope, accurate descriptions and applicable restrictions.
- [How to Add Products to Your Shop](https://seller-us.tiktok.com/university/essay?knowledge_id=6581713858676522): listing fields and product image/video upload guidance.
- [Product Detail Pages and Listing Quality Guidelines](https://seller-us.tiktok.com/university/essay?default_language=en&knowledge_id=481891871868714): quality tiers and category-specific information; distinguish quality advice from upload limits.
- [AI-Generated Content Restrictions and Requirements for Product Listings Images](https://seller-us.tiktok.com/university/essay?knowledge_id=5892224899909383): truthful product scale, appearance, quantities, supported effects and SKU consistency.

The listing guide and quality guide have previously presented different title limits. Preserve the source context and resolve the applicable limit rather than merging numeric snippets into a universal rule. Listing videos, paid ads and organic posts have different specifications; only listing videos are supported here.

Inspect comparable **product listings** for this workflow. Ad-library material can inform an explicitly labeled creative hypothesis but does not establish that a product listing converts well, and does not authorize generating paid ads under these profiles.

## Shopify official sources

- [Product media types](https://help.shopify.com/en/manual/products/product-media/product-media-types): supported media and upload requirements, including theme support.
- [Adding product media](https://help.shopify.com/en/manual/products/product-media/add-media): media handling and import limitations.
- [Uploading and managing files](https://help.shopify.com/en/manual/shopify-admin/productivity-tools/file-uploads): current technical file requirements.
- [Product details](https://help.shopify.com/en/manual/products/details): product fields and presentation context.
- [Behavior reports](https://help.shopify.com/en/manual/reports-and-analytics/shopify-reports/report-types/default-reports/behaviour-reports): definitions for store funnel/conversion metrics if the user supplies analytics.

Shopify is a customizable storefront. Obtain the actual theme/layout, responsive crops and destination country/language; do not invent a universal white-background rule, image ratio or copy template. Validate the storefront's product-page placement separately from Shop app, Google Shopping, Meta or other feeds. No merchant conversion data is public merely because the storefront can be browsed.

## Planned platform expansion — not currently supported

| Proposed milestone | Candidate scope | Work required before support |
| --- | --- | --- |
| First proposed expansion | Etsy US and eBay US listing content | Define categories and placements; research current image, copy and video rules; implement and verify profiles and export tests |
| Subsequent proposed expansion | Amazon UK/DE/JP; TikTok Shop UK | Add market-specific source packs, localization, category rules, disclosure handling and validated exports |
| Later | Shopee SG/MY, Lazada SG/MY, AliExpress US/EU | Establish market/placement coverage, official evidence access, supported AIsa research/generation routes and representative validation fixtures |

These are planning targets, not release commitments; there are no guaranteed dates. Do not label a roadmap platform supported until its capability has shipped and been verified. Each addition is gated on usable current AIsa operations, their input/output contracts, platform-source coverage and end-to-end validation. If AIsa coverage is missing, record the dependency instead of promising automatic support.

Useful official starting points for future research are [eBay picture policy](https://www.ebay.com/help/policies/selling-policies/listing-policy?id=4370), [Etsy image guidance](https://help.etsy.com/hc/en-us/articles/115015663347-Requirements-and-Best-Practices-for-Images-in-Your-Etsy-Shop) and [Etsy listing videos](https://help.etsy.com/hc/en-us/articles/360053206073-How-to-Add-Listing-Videos?segment=selling). Links alone do not constitute a supported workflow.
