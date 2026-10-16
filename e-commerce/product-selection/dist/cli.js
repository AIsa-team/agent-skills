#!/usr/bin/env node
import { readFile } from 'node:fs/promises';
import { calculatePricing, comparePrices } from './pricing.js';
import { object, planResearch, rankOpportunities } from './research.js';
const help = `Product selection helpers (Node.js >=22; no API key or network).
Usage: node dist/cli.js <plan|rank|price|compare-prices> <input.json|->
  plan           Generate scenario-specific AIsa MCP discovery intents.
  rank           Compare evidence-backed opportunities and feasibility gates.
  price          Calculate one pricing input, or {scenarios:[{name,input}]}.
  compare-prices Normalize prefiltered delivered-unit comparable prices.
  -              Read JSON from stdin. JSON results go to stdout.
Exit codes: 0 success; 2 invalid command/input or calculation error.
Examples:
  node dist/cli.js plan assets/explore-input.json
  node dist/cli.js price assets/pricing-example.json
No helper discovers credentials, performs network calls or executes MCP calls.`;
async function main() {
    const args = process.argv.slice(2);
    if (args.includes('--help') || args.includes('-h')) {
        console.log(help);
        return;
    }
    if (args.length !== 2 || !['plan', 'rank', 'price', 'compare-prices'].includes(args[0]))
        throw new Error(help);
    let source;
    if (args[1] === '-') {
        process.stdin.setEncoding('utf8');
        const chunks = [];
        for await (const chunk of process.stdin)
            chunks.push(String(chunk));
        source = chunks.join('');
    }
    else
        source = await readFile(args[1], 'utf8');
    let input;
    try {
        input = JSON.parse(source);
    }
    catch {
        throw new Error('Input must be valid JSON; use explicit numbers, null for unknown evidence, and no comments');
    }
    let output;
    if (args[0] === 'plan')
        output = planResearch(input);
    else if (args[0] === 'rank')
        output = rankOpportunities(input);
    else if (args[0] === 'compare-prices')
        output = comparePrices(input);
    else {
        const value = object(input, 'input');
        if ('scenarios' in value) {
            if (!Array.isArray(value.scenarios) || !value.scenarios.length)
                throw new Error('scenarios must be a nonempty array');
            const names = new Set();
            output = { scenarios: value.scenarios.map((raw, i) => {
                    const scenario = object(raw, `scenarios[${i}]`);
                    if (typeof scenario.name !== 'string' || !scenario.name.trim() || names.has(scenario.name))
                        throw new Error('Each scenario needs a unique nonempty name');
                    names.add(scenario.name);
                    return { name: scenario.name, result: calculatePricing(scenario.input) };
                }) };
        }
        else
            output = calculatePricing(input);
    }
    console.log(JSON.stringify(output, null, 2));
}
main().catch(error => { console.error(JSON.stringify({ error: error instanceof Error ? error.message : String(error) })); process.exitCode = 2; });
