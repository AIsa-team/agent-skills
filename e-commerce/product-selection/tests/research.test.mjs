import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { planResearch, rankOpportunities } from '../dist/research.js';

test('all entry scenarios preserve supplied market/product', () => {
  for (const [input, mode] of [[{}, 'explore'], [{markets:['Germany']}, 'market-first'], [{products:['travel organizer']}, 'product-first'], [{markets:['Germany'],products:['travel organizer']}, 'market-and-product']]) {
    const result = planResearch(input);
    assert.equal(result.mode, mode);
    assert.deepEqual(result.context.markets, input.markets ?? []);
    assert.deepEqual(result.context.products, input.products ?? []);
    assert.equal(result.mcpEndpoint, 'https://mcp.aisa.one/mcp');
    assert.ok(result.discovery.every(d => d.mcpTool === 'search'));
  }
});
const good = {id:'good',market:'DE',product:'organizer',channel:'Amazon',gates:{compliance:'pass',fulfillment:'pass',economics:'pass'},dimensions:Object.fromEntries(['demand','economics','competition','operations'].map(k=>[k,{score:3,evidence:['source-1']}]))};
test('failed gates cannot be compensated by high scores; missing evidence stays uncertain', () => {
  const blocked = {...good,id:'blocked',gates:{...good.gates,compliance:'fail'}};
  const unknown = {...good,id:'unknown',dimensions:{...good.dimensions,economics:null}};
  const result = rankOpportunities({opportunities:[blocked,unknown,good]}).opportunities;
  assert.deepEqual(result.map(r=>r.status), ['eligible-for-pilot','investigate','blocked']);
  assert.equal(result[0].lowerBound,60);
  assert.equal(result[1].evidenceCoverage,65);
  assert.equal(result[1].upperBound - result[1].lowerBound,35);
  assert.equal(result[2].lowerBound,null);
});
test('rejects invented numeric strings, scores without evidence and duplicate opportunity IDs', () => {
  assert.throws(()=>rankOpportunities({opportunities:[{...good,dimensions:{...good.dimensions,demand:{score:'5',evidence:['a']}}}]}), /0–5/);
  assert.throws(()=>rankOpportunities({opportunities:[{...good,dimensions:{...good.dimensions,demand:{score:5,evidence:[]}}}]}), /evidence/);
  assert.throws(()=>rankOpportunities({opportunities:[good,good]}), /duplicate/);
  for (const value of [['fail'], ['unknown'], null, true]) {
    assert.throws(()=>rankOpportunities({opportunities:[{...good,gates:{...good.gates,compliance:value}}]}), /gates.compliance/);
  }
});
test('shipped CLI emits JSON from stdin and separates invalid-input errors', () => {
  const valid = spawnSync(process.execPath,['dist/cli.js','plan','-'],{input:'{"markets":["Japan"]}',encoding:'utf8'});
  assert.equal(valid.status,0,valid.stderr);
  assert.equal(JSON.parse(valid.stdout).mode,'market-first');
  const invalid = spawnSync(process.execPath,['dist/cli.js','plan','-'],{input:'bad',encoding:'utf8'});
  assert.equal(invalid.status,2);
  assert.equal(invalid.stdout,'');
  assert.match(JSON.parse(invalid.stderr).error,/valid JSON/);
});
