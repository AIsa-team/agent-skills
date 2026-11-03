# Prompt guidance and progressive intake

Read this for incomplete prompts, user requests for examples, or intake ambiguity. The first invocation always begins with the concise greeting in SKILL.md. Follow-ups do not repeat it.

## Start with an ordinary sentence

Minimal prompt:

> 我想把小风扇卖到美国。

Equivalent:

> I want to sell canvas bags to Germany.

Do not ask users to rewrite a usable request into a template. Extract facts from text, attachments and prior turns; ask only for missing details that affect the answer. An attached product image can suggest a question, but it does not prove material, battery chemistry, certifications or intended age.

Optional template, offered when requested:

> 我准备在【时间】通过【平台及站点】向【国家/地区】销售【商品及用途】，帮我查需要满足的要求和上线前要准备的材料。

Optional extra detail:

> 从【发货地】发货，使用【直邮／FBA／海外仓】，主要面向【使用人群】，已有【检测报告／证书／包装资料】。

## Ask progressively

Maintain known facts, unresolved facts and questions already answered. Ask at most two questions in one turn, choosing the ones that most affect applicability. Do not force a fixed order when product risks change the priorities.

| Known input | Useful next move |
| --- | --- |
| Product only | Ask destination; ask target audience/use if needed to identify the product category. |
| Product and country | Ask intended launch period and platform/site, unless a product distinction is more urgent. Start scoped preliminary research if useful. |
| Product, destination, time and platform | State the scope and proceed; ask conditional questions as research identifies a dependency. |
| Unknown fulfilment or certificates | Explain which checks depend on them; continue unaffected checks. |
| Several products/markets | Preserve every requested combination; identify which facts can be reused and which need separate findings. |

Conditional facts include age group and intended use, composition/materials, battery/electrical/wireless features, food contact, claimed benefits, own-brand versus resale, manufacturing origin, seller domicile, shipping/storage country and importer role. Ask only about applicable branches. Do not require all of these before any research.

## Example conversations

**Minimal request**

User: 我想把小风扇卖到美国。

Assistant: 你好，我可以帮你查小风扇卖到美国需要满足的要求。这款风扇用什么供电，是否带电池？主要面向成人还是儿童使用？

User: 内置充电电池，给成人用。打算明年夏天在 TikTok Shop 卖。

Assistant (when today is 2026-11-03): 我会按成人用充电小风扇、2027 年夏季计划开售来查。TikTok Shop 是美国站吗？准备从中国直邮，还是使用海外仓？

Use the actual current year when interpreting the conversation. Preserve a known month as month precision (`YYYY-MM` in the local brief); keep an undefined season as a note. Do not invent an exact day. Ask for the shipping/import period only when it changes the assessment.

**Specific request**

User: 我计划 2027 年 1 月在 Amazon US 卖成人帆布包，中国直邮，帮我查上线前要准备什么。

Assistant: 你好，我可以帮你查出海销售要求。我会按成人帆布包、美国 Amazon US、2027 年 1 月开售、中国直邮来检查，先查相关法规和平台材料要求。

Proceed; no confirmation gate or duplicate question about destination/platform. Material composition or seller details can be requested when a specific requirement depends on them.

**Broad geography**

User: 想做 Shopify，卖保温杯到欧洲。

Assistant: 你好，我可以帮你查出海销售要求。准备先卖到欧洲哪些国家？保温杯主要给成人还是儿童使用？

If countries are undecided, offer an EU-level preliminary assessment with national checks pending. Europe also includes non-EU countries; do not silently equate the two.

**An unknown answer**

User: 还没决定用海外仓还是直邮。

Assistant: 发货和仓储方式会影响进口与税务责任。我先查两种方式都适用的商品和平台要求，把依赖发货方式的事项单独列出。

Do not treat “unknown” as refusal or restart intake. Keep the open question in the assessment.

## Timing and completeness

The four core dimensions are product, destination, selling period and platform. They need not all appear in the first message. Product plus destination can support preliminary research; missing timing or platform limits the corresponding conclusions.

Normalize unambiguous relative dates and tell the user the interpretation. For “春节后” or “later,” ask for a year/month when a transition rule makes it material. If the user asks about a past period, research rules in force then and identify the limits of current pages as historical evidence. Separate research date, planned sales, import date and first market placement where relevant.

End with a short scope statement and unresolved facts in the report. Do not make the user approve an internal research prompt, repeat answers or complete a mandatory long form.
