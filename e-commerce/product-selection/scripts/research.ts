/** Offline planning and evidence-aware comparison; never calls paid tools. */
type JsonObject = Record<string, unknown>;
export function object(value: unknown, field: string): JsonObject {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) throw new Error(`${field} must be an object`);
  return value as JsonObject;
}
function text(value: unknown, field: string): string {
  if (typeof value !== 'string' || !value.trim()) throw new Error(`${field} must be a nonempty string`);
  return value.trim();
}
function strings(value: unknown, field: string): string[] {
  if (value === undefined) return [];
  if (!Array.isArray(value)) throw new Error(`${field} must be an array`);
  return [...new Set(value.map((v, i) => text(v, `${field}[${i}]`)))];
}

export function planResearch(value: unknown) {
  const input = object(value, 'input');
  const markets = strings(input.markets, 'markets');
  const products = strings(input.products, 'products');
  const channels = strings(input.channels, 'channels');
  const mode = markets.length ? (products.length ? 'market-and-product' : 'market-first') : (products.length ? 'product-first' : 'explore');
  const context = JSON.stringify({ markets, products, channels });
  const intents = [
    { id: 'official-research', purpose: 'Country/channel feasibility, trade flows, tax/customs and product rules', query: `Tavily search extract official trade customs ecommerce regulations ${context}` },
    { id: 'localized-demand', purpose: 'Country/language keyword demand and seasonality; verify supported locations first', query: `DataForSEO locations languages Google keyword search volume Google Trends Amazon Labs related keywords ${context}` },
    { id: 'competitor-prices', purpose: 'Comparable listings, seller prices, variants and review problems', query: `DataForSEO Merchant Amazon Google products product details sellers reviews ${context}` }
  ];
  if (channels.some(c => /store|shopify|direct|dtc|website/i.test(c))) {
    intents.push({ id: 'channel-fit', purpose: 'Website country mix and acquisition channels; site-level estimates', query: `Similarweb website top geographies marketing channels traffic engagement ${context}` });
  }
  return {
    mode, context: { markets, products, channels },
    questions: ['Seller origin, sourcing strengths, budget and inventory tolerance', 'Target channel, fulfillment route, product dimensions/materials and restrictions', 'Unit costs, currency, profit goal and permitted data spend'],
    scope: mode === 'explore' ? 'Screen 3–5 market hypotheses and 2–3 product families, then research the strongest pairs' : mode === 'market-first' ? 'Keep the selected market fixed; screen product families and channels' : mode === 'product-first' ? 'Keep the product fixed; compare 3–5 feasible market/channel combinations' : 'Assess the specified pair and viable channels',
    mcpEndpoint: 'https://mcp.aisa.one/mcp',
    next: 'Use each intent with native search at the configured MCP endpoint; resolve operation IDs and get_details schemas/prices, then use within authorized spend',
    discovery: intents.map(intent => ({ ...intent, mcpTool: 'search', arguments: { query: intent.query } })),
    cautions: ['This is a research plan, not live evidence or a batch of executable provider calls', 'No seller origin, candidate countries, costs, tool IDs, rates or data budget are silently assumed', 'A chosen market or product stays fixed unless the user asks for alternatives']
  };
}

const weights = { demand: 0.25, economics: 0.35, competition: 0.20, operations: 0.20 } as const;
type Dimension = keyof typeof weights;
export function rankOpportunities(value: unknown) {
  const input = object(value, 'input');
  if (!Array.isArray(input.opportunities) || input.opportunities.length === 0) throw new Error('opportunities must be a nonempty array');
  const seen = new Set<string>();
  const rows = input.opportunities.map((raw, index) => {
    const row = object(raw, `opportunities[${index}]`);
    const id = text(row.id, 'id');
    if (seen.has(id)) throw new Error(`duplicate opportunity id: ${id}`);
    seen.add(id);
    const market = text(row.market, 'market'), product = text(row.product, 'product'), channel = text(row.channel, 'channel');
    const gates = object(row.gates, 'gates');
    for (const gate of ['compliance', 'fulfillment', 'economics']) {
      if (typeof gates[gate] !== 'string' || !['pass', 'fail', 'unknown'].includes(gates[gate] as string)) throw new Error(`gates.${gate} must be pass, fail or unknown`);
    }
    const dimensions = object(row.dimensions, 'dimensions');
    let lowerBound = 0, coverage = 0;
    const missing: string[] = [];
    for (const [key, weight] of Object.entries(weights) as [Dimension, number][]) {
      const rawDimension = dimensions[key];
      if (rawDimension === null || rawDimension === undefined) { missing.push(key); continue; }
      const dimension = object(rawDimension, `dimensions.${key}`);
      if (typeof dimension.score !== 'number' || !Number.isFinite(dimension.score) || dimension.score < 0 || dimension.score > 5) throw new Error(`${key}.score must be 0–5`);
      const evidence = strings(dimension.evidence, `${key}.evidence`);
      if (!evidence.length) throw new Error(`${key}.evidence must contain source/evidence IDs; use null for unknown`);
      lowerBound += weight * dimension.score * 20;
      coverage += weight;
    }
    const gateValues = ['compliance', 'fulfillment', 'economics'].map(k => gates[k]);
    const status = gateValues.includes('fail') ? 'blocked' : gateValues.includes('unknown') || missing.length ? 'investigate' : 'eligible-for-pilot';
    const round = (n: number) => Math.round(n * 100) / 100;
    return { id, market, product, channel, gates, dimensions, status,
      lowerBound: status === 'blocked' ? null : round(lowerBound),
      upperBound: status === 'blocked' ? null : round(lowerBound + (1 - coverage) * 100),
      evidenceCoverage: round(coverage * 100), missing,
      explanation: 'Heuristic score interval, not a probability, market forecast or compliance certification' };
  });
  const order: Record<string, number> = { 'eligible-for-pilot': 0, investigate: 1, blocked: 2 };
  rows.sort((a, b) => order[a.status] - order[b.status] || (b.lowerBound ?? -1) - (a.lowerBound ?? -1) || a.id.localeCompare(b.id));
  return { weights, opportunities: rows, caveat: 'Review score rationales and overlapping intervals; missing evidence never receives a neutral score. Pilot eligibility still requires seller authorization.' };
}
