// index.ts — AIsa Multi Search Engine Plugin for OpenClaw
// Powered by AIsa API (https://docs.aisa.one)
//
// Provides multi-source search tools:
//   - aisa_web_search        — Web search via AIsa Scholar Web endpoint
//   - aisa_scholar_search    — Academic paper search via AIsa Scholar endpoint
//   - aisa_smart_search      — Intelligent hybrid search (web + academic)
//   - aisa_tavily_search     — Tavily web search with advanced filtering
//   - aisa_tavily_extract    — Extract content from URLs via Tavily
//   - aisa_perplexity_search — Deep research via Perplexity Sonar models
//   - aisa_multi_search      — Parallel multi-source search with confidence scoring

import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import { Type } from "@sinclair/typebox";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const AISA_BASE = "https://api.aisa.one/apis/v1";

interface PluginConfig {
  aisaApiKey?: string;
  defaultMaxResults?: number;
  defaultSearchDepth?: string;
}

function getApiKey(config: PluginConfig): string {
  const key = config.aisaApiKey || process.env.AISA_API_KEY || "";
  if (!key) {
    throw new Error(
      "AISA_API_KEY is not configured. Set it in plugin config or as an environment variable. " +
        "Get your key at https://aisa.one",
    );
  }
  return key;
}

async function aisaPost(
  apiKey: string,
  path: string,
  body: Record<string, unknown>,
): Promise<unknown> {
  const url = `${AISA_BASE}${path}`;
  const res = await fetch(url, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`AIsa API error ${res.status} on ${path}: ${text}`);
  }
  return res.json();
}

async function aisaGet(
  apiKey: string,
  path: string,
  params: Record<string, string>,
): Promise<unknown> {
  const qs = new URLSearchParams(params).toString();
  const url = `${AISA_BASE}${path}${qs ? `?${qs}` : ""}`;
  const res = await fetch(url, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      Accept: "application/json",
    },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`AIsa API error ${res.status} on ${path}: ${text}`);
  }
  return res.json();
}

function formatResults(data: unknown, source: string): string {
  const obj = data as Record<string, unknown>;
  const lines: string[] = [`## ${source} Results\n`];

  // Handle Tavily-style results
  if (Array.isArray(obj.results)) {
    for (const r of obj.results as Record<string, unknown>[]) {
      lines.push(`### ${r.title || "Untitled"}`);
      if (r.url) lines.push(`**URL:** ${r.url}`);
      if (r.published_date) lines.push(`**Date:** ${r.published_date}`);
      if (r.content) lines.push(`\n${r.content}\n`);
      else if (r.snippet) lines.push(`\n${r.snippet}\n`);
      lines.push("---");
    }
  }

  // Handle Scholar-style results with organic_results
  if (Array.isArray(obj.organic_results)) {
    for (const r of obj.organic_results as Record<string, unknown>[]) {
      lines.push(`### ${r.title || "Untitled"}`);
      if (r.link) lines.push(`**URL:** ${r.link}`);
      if (r.publication_info)
        lines.push(
          `**Publication:** ${JSON.stringify(r.publication_info)}`,
        );
      if (r.snippet) lines.push(`\n${r.snippet}\n`);
      lines.push("---");
    }
  }

  // Handle answer field (Tavily include_answer or Perplexity)
  if (obj.answer) {
    lines.push(`\n**Answer:** ${obj.answer}\n`);
  }

  // Handle Perplexity-style choices
  if (Array.isArray(obj.choices)) {
    for (const c of obj.choices as Record<string, unknown>[]) {
      const msg = c.message as Record<string, unknown> | undefined;
      if (msg?.content) {
        lines.push(`\n${msg.content}\n`);
      }
    }
  }

  // Handle citations
  if (Array.isArray(obj.citations)) {
    lines.push("\n**Citations:**");
    for (const cite of obj.citations as string[]) {
      lines.push(`- ${cite}`);
    }
  }

  // Handle usage/cost info
  if (obj.usage) {
    const usage = obj.usage as Record<string, unknown>;
    if (usage.cost !== undefined) {
      lines.push(`\n*Cost: $${usage.cost}*`);
    }
  }

  if (lines.length <= 1) {
    lines.push("No results found.");
    lines.push(`\nRaw response:\n\`\`\`json\n${JSON.stringify(data, null, 2)}\n\`\`\``);
  }

  return lines.join("\n");
}

// ---------------------------------------------------------------------------
// Plugin Entry
// ---------------------------------------------------------------------------

export default definePluginEntry({
  id: "aisa-multi-search-engine",
  name: "AIsa Multi Search Engine",
  description:
    "Multi-source search powered by AIsa API — web, academic, Tavily, and Perplexity in one plugin.",

  register(api) {
    const config = (api as unknown as { config: PluginConfig }).config ?? {};

    // -----------------------------------------------------------------------
    // Tool 1: Web Search (AIsa Scholar Web)
    // -----------------------------------------------------------------------
    api.registerTool({
      name: "aisa_web_search",
      description:
        "Search the web using AIsa Scholar Web endpoint. Returns structured web results with titles, URLs, and snippets.",
      parameters: Type.Object({
        query: Type.String({ description: "Search query" }),
        max_results: Type.Optional(
          Type.Integer({
            description: "Maximum results (1-100, default 10)",
            minimum: 1,
            maximum: 100,
          }),
        ),
      }),
      async execute(_id, params) {
        const apiKey = getApiKey(config);
        const maxResults =
          params.max_results ?? config.defaultMaxResults ?? 10;
        const data = await aisaPost(apiKey, "/scholar/search/web", {
          query: params.query,
          max_num_results: maxResults,
        });
        const text = formatResults(data, "Web Search");
        return { content: [{ type: "text", text }] };
      },
    });

    // -----------------------------------------------------------------------
    // Tool 2: Scholar Search (Academic Papers)
    // -----------------------------------------------------------------------
    api.registerTool({
      name: "aisa_scholar_search",
      description:
        "Search academic papers and scholarly articles via AIsa Scholar endpoint. Supports year range filtering.",
      parameters: Type.Object({
        query: Type.String({ description: "Academic search query" }),
        max_results: Type.Optional(
          Type.Integer({
            description: "Maximum results (1-100, default 10)",
            minimum: 1,
            maximum: 100,
          }),
        ),
        year_from: Type.Optional(
          Type.Integer({ description: "Year lower bound (e.g. 2023)" }),
        ),
        year_to: Type.Optional(
          Type.Integer({ description: "Year upper bound (e.g. 2025)" }),
        ),
      }),
      async execute(_id, params) {
        const apiKey = getApiKey(config);
        const maxResults =
          params.max_results ?? config.defaultMaxResults ?? 10;
        const body: Record<string, unknown> = {
          query: params.query,
          max_num_results: maxResults,
        };
        if (params.year_from) body.as_ylo = params.year_from;
        if (params.year_to) body.as_yhi = params.year_to;
        const data = await aisaPost(apiKey, "/scholar/search/scholar", body);
        const text = formatResults(data, "Scholar Search");
        return { content: [{ type: "text", text }] };
      },
    });

    // -----------------------------------------------------------------------
    // Tool 3: Smart Search (Hybrid Web + Academic)
    // -----------------------------------------------------------------------
    api.registerTool({
      name: "aisa_smart_search",
      description:
        "Intelligent hybrid search combining web and academic sources via AIsa Smart Search endpoint.",
      parameters: Type.Object({
        query: Type.String({ description: "Search query" }),
        max_results: Type.Optional(
          Type.Integer({
            description: "Maximum results (1-100, default 10)",
            minimum: 1,
            maximum: 100,
          }),
        ),
      }),
      async execute(_id, params) {
        const apiKey = getApiKey(config);
        const maxResults =
          params.max_results ?? config.defaultMaxResults ?? 10;
        const data = await aisaPost(apiKey, "/scholar/search/smart", {
          query: params.query,
          max_num_results: maxResults,
        });
        const text = formatResults(data, "Smart Search");
        return { content: [{ type: "text", text }] };
      },
    });

    // -----------------------------------------------------------------------
    // Tool 4: Tavily Search (Advanced Web Search)
    // -----------------------------------------------------------------------
    api.registerTool({
      name: "aisa_tavily_search",
      description:
        "Advanced web search via Tavily through AIsa API. Supports search depth, topic filtering, time ranges, domain inclusion/exclusion, and LLM-generated answers.",
      parameters: Type.Object({
        query: Type.String({ description: "Search query" }),
        search_depth: Type.Optional(
          Type.String({
            description: "Search depth: basic, advanced, fast, or ultra-fast",
            enum: ["basic", "advanced", "fast", "ultra-fast"],
          }),
        ),
        max_results: Type.Optional(
          Type.Integer({
            description: "Maximum results (1-20, default 5)",
            minimum: 1,
            maximum: 20,
          }),
        ),
        topic: Type.Optional(
          Type.String({
            description: "Topic category: general, news, or finance",
            enum: ["general", "news", "finance"],
          }),
        ),
        time_range: Type.Optional(
          Type.String({
            description:
              "Time range filter: day, week, month, year, or d/w/m/y shorthand",
          }),
        ),
        include_answer: Type.Optional(
          Type.Boolean({
            description: "Include an LLM-generated answer (default false)",
          }),
        ),
        include_domains: Type.Optional(
          Type.Array(Type.String(), {
            description: "Domains to include in results",
          }),
        ),
        exclude_domains: Type.Optional(
          Type.Array(Type.String(), {
            description: "Domains to exclude from results",
          }),
        ),
        country: Type.Optional(
          Type.String({
            description:
              "Boost results from a specific country (ISO 3166-1 alpha-2 code)",
          }),
        ),
      }),
      async execute(_id, params) {
        const apiKey = getApiKey(config);
        const body: Record<string, unknown> = {
          query: params.query,
          search_depth:
            params.search_depth ?? config.defaultSearchDepth ?? "basic",
          max_results: params.max_results ?? 5,
        };
        if (params.topic) body.topic = params.topic;
        if (params.time_range) body.time_range = params.time_range;
        if (params.include_answer !== undefined)
          body.include_answer = params.include_answer;
        if (params.include_domains)
          body.include_domains = params.include_domains;
        if (params.exclude_domains)
          body.exclude_domains = params.exclude_domains;
        if (params.country) body.country = params.country;

        const data = await aisaPost(apiKey, "/tavily/search", body);
        const text = formatResults(data, "Tavily Search");
        return { content: [{ type: "text", text }] };
      },
    });

    // -----------------------------------------------------------------------
    // Tool 5: Tavily Extract (Content Extraction from URLs)
    // -----------------------------------------------------------------------
    api.registerTool({
      name: "aisa_tavily_extract",
      description:
        "Extract clean content from one or more URLs using Tavily Extract via AIsa API. Useful for reading full articles.",
      parameters: Type.Object({
        urls: Type.Array(Type.String(), {
          description: "List of URLs to extract content from",
        }),
      }),
      async execute(_id, params) {
        const apiKey = getApiKey(config);
        const data = await aisaPost(apiKey, "/tavily/extract", {
          urls: params.urls,
        });
        const obj = data as Record<string, unknown>;
        const lines: string[] = ["## Tavily Extract Results\n"];
        if (Array.isArray(obj.results)) {
          for (const r of obj.results as Record<string, unknown>[]) {
            lines.push(`### ${r.url || "Unknown URL"}`);
            if (r.raw_content)
              lines.push(
                `\n${(r.raw_content as string).slice(0, 3000)}\n`,
              );
            lines.push("---");
          }
        } else {
          lines.push(
            `\`\`\`json\n${JSON.stringify(data, null, 2)}\n\`\`\``,
          );
        }
        return { content: [{ type: "text", text: lines.join("\n") }] };
      },
    });

    // -----------------------------------------------------------------------
    // Tool 6: Perplexity Search (Deep Research)
    // -----------------------------------------------------------------------
    api.registerTool({
      name: "aisa_perplexity_search",
      description:
        "Deep research using Perplexity Sonar models via AIsa API. Provides synthesized answers with citations. Models: sonar (fast), sonar-pro (detailed), sonar-reasoning-pro (complex reasoning), sonar-deep-research (exhaustive).",
      parameters: Type.Object({
        query: Type.String({ description: "Research question or query" }),
        model: Type.Optional(
          Type.String({
            description:
              "Perplexity model: sonar, sonar-pro, sonar-reasoning-pro, or sonar-deep-research",
            enum: [
              "sonar",
              "sonar-pro",
              "sonar-reasoning-pro",
              "sonar-deep-research",
            ],
          }),
        ),
      }),
      async execute(_id, params) {
        const apiKey = getApiKey(config);
        const model = params.model ?? "sonar";

        // Map model names to AIsa API endpoints
        const endpointMap: Record<string, string> = {
          sonar: "/sonar",
          "sonar-pro": "/sonar-pro",
          "sonar-reasoning-pro": "/sonar-reasoning-pro",
          "sonar-deep-research": "/sonar-deep-research",
        };
        const endpoint = endpointMap[model] ?? "/sonar";

        const data = await aisaPost(apiKey, endpoint, {
          model,
          messages: [{ role: "user", content: params.query }],
        });
        const text = formatResults(data, `Perplexity (${model})`);
        return { content: [{ type: "text", text }] };
      },
    });

    // -----------------------------------------------------------------------
    // Tool 7: Multi Search (Parallel multi-source with confidence scoring)
    // -----------------------------------------------------------------------
    api.registerTool({
      name: "aisa_multi_search",
      description:
        "Parallel multi-source search combining web, scholar, smart, and Tavily results with confidence scoring. Best for comprehensive research requiring cross-source validation.",
      parameters: Type.Object({
        query: Type.String({ description: "Search query" }),
        max_results: Type.Optional(
          Type.Integer({
            description: "Maximum results per source (1-20, default 5)",
            minimum: 1,
            maximum: 20,
          }),
        ),
        include_scholar: Type.Optional(
          Type.Boolean({
            description: "Include academic/scholar results (default true)",
          }),
        ),
        include_tavily: Type.Optional(
          Type.Boolean({
            description: "Include Tavily results (default true)",
          }),
        ),
        include_explanation: Type.Optional(
          Type.Boolean({
            description:
              "Include AIsa Explain meta-analysis with confidence scoring (default true)",
          }),
        ),
      }),
      async execute(_id, params) {
        const apiKey = getApiKey(config);
        const maxResults = params.max_results ?? 5;
        const includeScholar = params.include_scholar !== false;
        const includeTavily = params.include_tavily !== false;
        const includeExplanation = params.include_explanation !== false;

        // Phase 1: Parallel retrieval
        const tasks: Promise<{ source: string; data: unknown }>[] = [];

        // Always include web search
        tasks.push(
          aisaPost(apiKey, "/scholar/search/web", {
            query: params.query,
            max_num_results: maxResults,
          }).then((data) => ({ source: "Web", data })),
        );

        // Always include smart search
        tasks.push(
          aisaPost(apiKey, "/scholar/search/smart", {
            query: params.query,
            max_num_results: maxResults,
          }).then((data) => ({ source: "Smart", data })),
        );

        if (includeScholar) {
          tasks.push(
            aisaPost(apiKey, "/scholar/search/scholar", {
              query: params.query,
              max_num_results: maxResults,
            }).then((data) => ({ source: "Scholar", data })),
          );
        }

        if (includeTavily) {
          tasks.push(
            aisaPost(apiKey, "/tavily/search", {
              query: params.query,
              max_results: maxResults,
              include_answer: true,
            }).then((data) => ({ source: "Tavily", data })),
          );
        }

        const results = await Promise.allSettled(tasks);
        const sections: string[] = [
          `# Multi-Source Search: "${params.query}"\n`,
        ];
        const successfulResults: Record<string, unknown>[] = [];

        for (const result of results) {
          if (result.status === "fulfilled") {
            const { source, data } = result.value;
            sections.push(formatResults(data, source));
            successfulResults.push(data as Record<string, unknown>);
          } else {
            sections.push(`\n> Search source failed: ${result.reason}\n`);
          }
        }

        // Phase 2: Confidence scoring (deterministic)
        const totalSources = results.filter(
          (r) => r.status === "fulfilled",
        ).length;
        let confidenceScore = 0;

        // Source availability (40%)
        confidenceScore += (totalSources / tasks.length) * 40;

        // Result count quality (35%)
        let totalResults = 0;
        for (const d of successfulResults) {
          if (Array.isArray(d.results)) totalResults += d.results.length;
          if (Array.isArray(d.organic_results))
            totalResults += d.organic_results.length;
        }
        const expectedResults = maxResults * tasks.length;
        confidenceScore +=
          Math.min(totalResults / expectedResults, 1) * 35;

        // Source diversity (15%)
        const hasScholar = successfulResults.some((d) =>
          Array.isArray(d.organic_results),
        );
        const hasWeb = successfulResults.some(
          (d) =>
            Array.isArray(d.results) &&
            !Array.isArray(d.organic_results),
        );
        const diversityScore =
          (hasScholar ? 0.5 : 0) + (hasWeb ? 0.5 : 0);
        confidenceScore += diversityScore * 15;

        // Recency bonus (10%)
        confidenceScore += totalSources > 0 ? 10 : 0;

        confidenceScore = Math.min(Math.round(confidenceScore), 100);

        // Confidence interpretation
        let confidenceLevel: string;
        if (confidenceScore >= 90) confidenceLevel = "Very High";
        else if (confidenceScore >= 70) confidenceLevel = "High";
        else if (confidenceScore >= 50) confidenceLevel = "Medium";
        else if (confidenceScore >= 30) confidenceLevel = "Low";
        else confidenceLevel = "Very Low";

        sections.push(`\n## Confidence Assessment`);
        sections.push(`- **Score:** ${confidenceScore}/100`);
        sections.push(`- **Level:** ${confidenceLevel}`);
        sections.push(
          `- **Sources queried:** ${tasks.length} | **Successful:** ${totalSources}`,
        );
        sections.push(`- **Total results:** ${totalResults}`);

        // Phase 3: Optional explanation via AIsa Explain
        if (includeExplanation && successfulResults.length > 0) {
          try {
            const explainData = await aisaPost(
              apiKey,
              "/scholar/explain",
              {
                results: successfulResults,
                language: "en",
                format: "summary",
              },
            );
            const explainObj = explainData as Record<string, unknown>;
            if (explainObj.summary) {
              sections.push(`\n## AI Synthesis\n`);
              sections.push(explainObj.summary as string);
            }
            if (Array.isArray(explainObj.citations)) {
              sections.push(`\n**Citations:**`);
              for (const c of explainObj.citations as string[]) {
                sections.push(`- ${c}`);
              }
            }
          } catch {
            sections.push(
              `\n> *Explanation generation skipped (API error).*`,
            );
          }
        }

        return { content: [{ type: "text", text: sections.join("\n") }] };
      },
    });
  },
});
