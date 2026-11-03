import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const cli = fileURLToPath(new URL('../dist/cli.js', import.meta.url));
const readExample = name => JSON.parse(readFileSync(new URL(`../assets/${name}.example.json`, import.meta.url), 'utf8'));
const brief = () => ({
  schemaVersion: 1,
  asOf: '2026-11-03',
  product: { name: 'Synthetic adult canvas bag', facts: ['Test fixture only'] },
  destinations: [{ country: 'DE', platforms: [{ name: 'Shopify' }] }],
  plannedSale: { start: '2027-01-01', end: '2027-03-31' },
});
const assessment = () => ({
  schemaVersion: 1,
  synthetic: true,
  brief: brief(),
  scope: 'Synthetic case for document consistency tests; no researched legal rule',
  evidence: [{
    id: 'official', title: 'Synthetic official source fixture', url: 'https://example.com/source',
    authority: 'regulator', jurisdictions: ['EU'], accessedAt: '2026-11-03',
    excerpt: 'Synthetic fixture text, not a real regulation.', inspected: true,
  }],
  findings: [{
    id: 'f1', title: 'Synthetic scoped finding', scope: 'Only the supplied fixture record',
    status: 'issue-found', kind: 'law', jurisdiction: 'DE', sourceIds: ['official'],
    explanation: 'Fixture result only.', action: 'Replace all fixtures with inspected real evidence.',
    applicability: { reason: 'Synthetic fixture applicability.', temporalStatus: 'applies', ruleStatus: 'enacted', effectiveFrom: '2026-12-01' },
  }],
});

function run(command, data) {
  const directory = mkdtempSync(join(tmpdir(), 'compliance-checker-test-'));
  try {
    const input = join(directory, 'input.json');
    const contents = JSON.stringify(data);
    writeFileSync(input, contents);
    const result = spawnSync(process.execPath, [cli, command, input], { encoding: 'utf8' });
    assert.equal(readFileSync(input, 'utf8'), contents, 'CLI must not modify the input');
    assert.deepEqual(readdirSync(directory), ['input.json'], 'CLI must not create output files');
    return result;
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
}

function success(command, data) {
  const result = run(command, data);
  assert.equal(result.status, 0, result.stderr);
  assert.equal(result.stderr, '');
  return command === 'render' ? result.stdout : JSON.parse(result.stdout);
}

function failure(data) {
  const result = run('validate', data);
  assert.equal(result.status, 1);
  assert.equal(result.stdout, '');
  const output = JSON.parse(result.stderr);
  assert.equal(output.valid, false);
  assert.ok(output.errors.length > 0);
}

test('product and destination start research; only two pending questions are returned', () => {
  const result = success('inspect-brief', readExample('brief'));
  assert.equal(result.readyToResearch, true);
  assert.equal(result.preliminary, true);
  assert.deepEqual(result.missingCoreFields, ['plannedSale.start', 'destinations[0].platforms']);
  assert.deepEqual(result.nextQuestions.map(q => q.field), result.missingCoreFields);
  assert.ok(result.nextQuestions.length <= 2);
});

test('minimal brief is valid and prioritizes product/destination questions', () => {
  const result = success('inspect-brief', { schemaVersion: 1, asOf: '2026-11-03' });
  assert.equal(result.readyToResearch, false);
  assert.equal(result.preliminary, true);
  assert.deepEqual(result.nextQuestions.map(q => q.field), ['product.name', 'destinations']);
});

test('known fields are not asked again and Shopify does not need a regional site', () => {
  const result = success('inspect-brief', brief());
  assert.equal(result.readyToResearch, true);
  assert.equal(result.preliminary, false);
  assert.deepEqual(result.missingCoreFields, []);
  assert.deepEqual(result.nextQuestions, []);
});

test('missing platform for a second destination is still identified', () => {
  const b = brief();
  b.destinations.push({ country: 'US' });
  const result = success('inspect-brief', b);
  assert.deepEqual(result.missingCoreFields, ['destinations[1].platforms']);
  assert.equal(result.preliminary, true);
});

test('EU baseline research can start while specific countries remain pending', () => {
  const b = brief();
  b.destinations[0].country = 'EU';
  const result = success('inspect-brief', b);
  assert.equal(result.readyToResearch, true);
  assert.equal(result.preliminary, true);
  assert.deepEqual(result.missingCoreFields, ['destinations[0].country']);
  assert.equal(result.nextQuestions[0].field, 'destinations[0].country');
  const a = assessment();
  a.brief = b;
  a.findings[0].jurisdiction = 'EU';
  assert.equal(success('validate', a).preliminary, true);
});

test('EU placeholder does not silently establish a specific national destination', () => {
  const a = assessment();
  a.brief.destinations[0].country = 'EU';
  failure(a);
});

test('ambiguous Europe text is not automatically treated as EU', () => {
  const b = brief();
  b.destinations[0].country = 'Europe';
  assert.equal(run('inspect-brief', b).status, 1);
});

test('unknown timing remains pending without invented dates', () => {
  const b = brief();
  b.plannedSale = { note: 'Date unknown; ask later' };
  const result = success('inspect-brief', b);
  assert.deepEqual(result.missingCoreFields, ['plannedSale.start']);
  assert.equal(result.readyToResearch, true);
});

test('month precision satisfies timing intake and is preserved in the report', () => {
  const a = assessment();
  a.brief.plannedSale = { start: '2027-01', end: '2027-03' };
  const intake = success('inspect-brief', a.brief);
  assert.deepEqual(intake.missingCoreFields, []);
  assert.deepEqual(intake.nextQuestions, []);
  assert.equal(success('validate', a).valid, true);
  const output = success('render', a);
  assert.ok(output.includes('Planned sales: 2027-01 → 2027-03'));
  assert.ok(!output.includes('Planned sales: 2027-01-01'));
});

test('mixed date and month precision accepts possible same-month intervals', () => {
  for (const plannedSale of [
    { start: '2027-03-31', end: '2027-03' },
    { start: '2027-03', end: '2027-03-01' },
    { start: '2028-02-29', end: '2028-02' },
  ]) {
    const b = brief();
    b.plannedSale = plannedSale;
    assert.deepEqual(success('inspect-brief', b).missingCoreFields, []);
  }
});

test('out-of-period assertions work with only the boundaries that prove exclusion', () => {
  for (const [plannedSale, effective] of [
    [{ start: '2027-01' }, { effectiveTo: '2026-12-31' }],
    [{ end: '2027-03' }, { effectiveFrom: '2027-04-01' }],
  ]) {
    const a = assessment();
    a.brief.plannedSale = plannedSale;
    a.findings[0].status = 'not-applicable';
    a.findings[0].applicability = {
      reason: 'Synthetic disjoint interval.', temporalStatus: 'outside-period', ruleStatus: 'enacted', ...effective,
    };
    assert.equal(success('validate', a).valid, true);
  }
});

test('shipped example remains preliminary and unverified', () => {
  const result = success('validate', readExample('assessment'));
  assert.equal(result.valid, true);
  assert.equal(result.preliminary, true);
  assert.equal(result.coverage, 'partial');
  assert.equal(result.inspectedSources, 0);
});

test('empty findings are unchecked even when intake fields are complete', () => {
  const a = assessment();
  a.findings = [];
  a.evidence = [];
  const result = success('validate', a);
  assert.equal(result.preliminary, true);
  assert.equal(result.coverage, 'unchecked');
  assert.equal(result.findings, 0);
});

test('enacted future rule can apply to an explicitly future selling period', () => {
  const result = success('validate', assessment());
  assert.equal(result.valid, true);
  assert.equal(result.coverage, 'partial');
});

test('proposals can be recorded as uncertain, insufficient evidence', () => {
  const a = assessment();
  a.findings[0].status = 'insufficient-evidence';
  a.findings[0].applicability.ruleStatus = 'proposed';
  a.findings[0].applicability.temporalStatus = 'uncertain';
  assert.equal(success('validate', a).preliminary, true);
});

const invalidCases = {
  'impossible calendar date': a => { a.brief.plannedSale.start = '2027-02-30'; },
  'invalid calendar month': a => { a.brief.plannedSale.start = '2027-13'; },
  'zero calendar month': a => { a.brief.plannedSale.end = '2027-00'; },
  'reversed month precision period': a => { a.brief.plannedSale = { start: '2027-04', end: '2027-03' }; },
  'reversed mixed precision period': a => { a.brief.plannedSale = { start: '2027-04-01', end: '2027-03' }; },
  'month precision source date': a => { a.evidence[0].accessedAt = '2026-11'; },
  'month precision assessment date': a => { a.brief.asOf = '2026-11'; },
  'month precision effective date': a => { a.findings[0].applicability.effectiveFrom = '2026-12'; },
  'reversed planned period': a => { a.brief.plannedSale.end = '2026-01-01'; },
  'source retrieved after the assessment': a => { a.evidence[0].accessedAt = '2026-11-04'; },
  'nonexistent source ID': a => { a.findings[0].sourceIds = ['missing']; },
  'duplicate evidence IDs': a => { a.evidence.push(structuredClone(a.evidence[0])); },
  'unsupported confidence field': a => { a.findings[0].confidence = 0.99; },
  'unknown status pretending to clear compliance': a => { a.findings[0].status = 'compliant'; },
  'unsafe source URL protocol': a => { a.evidence[0].url = 'javascript:alert(1)'; },
  'credential-bearing source URL': a => { a.evidence[0].url = 'https://user:password@example.com'; },
  'uninspected source supporting no issue': a => { a.evidence[0].inspected = false; a.findings[0].status = 'no-issue-found'; },
  'non-authoritative source supporting legal conclusion': a => { a.evidence[0].authority = 'other'; },
  'platform source supporting law': a => { a.evidence[0].authority = 'platform'; },
  'source without declared jurisdiction': a => { a.evidence[0].jurisdictions = []; },
  'source/finding jurisdiction mismatch': a => { a.evidence[0].jurisdictions = ['US']; },
  'national source presented as EU-wide': a => { a.evidence[0].jurisdictions = ['DE']; a.findings[0].jurisdiction = 'EU'; },
  'finding outside destination scope': a => { a.findings[0].jurisdiction = 'US'; },
  'invalid destination code': a => { a.brief.destinations[0].country = 'ZZ'; },
  'future rule outside selling period': a => { a.findings[0].applicability.effectiveFrom = '2028-01-01'; },
  'expired rule outside selling period': a => { a.findings[0].applicability.effectiveFrom = '2020-01-01'; a.findings[0].applicability.effectiveTo = '2026-01-01'; },
  'reversed effective period': a => { a.findings[0].applicability.effectiveTo = '2020-01-01'; },
  'proposal presented as binding issue': a => { a.findings[0].applicability.ruleStatus = 'proposed'; },
  'uncertain timing presented as no issue': a => { a.findings[0].status = 'no-issue-found'; a.findings[0].applicability.temporalStatus = 'uncertain'; },
  'uninspected additional citation presented as substantiated': a => { const e = structuredClone(a.evidence[0]); e.id = 'unread'; e.inspected = false; a.evidence.push(e); a.findings[0].sourceIds.push('unread'); },
  'future applicability without a selling date': a => { delete a.brief.plannedSale; },
  'outside period with overlapping open-ended rule': a => {
    a.findings[0].status = 'not-applicable';
    a.findings[0].applicability.temporalStatus = 'outside-period';
    a.findings[0].applicability.effectiveFrom = '2027-02-01';
  },
  'outside period without effective bounds': a => {
    a.findings[0].status = 'not-applicable';
    a.findings[0].applicability.temporalStatus = 'outside-period';
    delete a.findings[0].applicability.effectiveFrom;
  },
  'outside period when boundaries touch': a => {
    a.findings[0].status = 'not-applicable';
    a.findings[0].applicability.temporalStatus = 'outside-period';
    a.findings[0].applicability.effectiveTo = '2027-01-01';
  },
  'outside period when month end still overlaps': a => {
    a.brief.plannedSale = { start: '2027-01', end: '2027-03' };
    a.findings[0].status = 'not-applicable';
    a.findings[0].applicability.temporalStatus = 'outside-period';
    a.findings[0].applicability.effectiveFrom = '2027-03-31';
  },
};
for (const [name, change] of Object.entries(invalidCases)) {
  test(`rejects ${name}`, () => { const a = assessment(); change(a); failure(a); });
}

test('renderer preserves the submitted scope, sources, actions and pending coverage', () => {
  const a = readExample('assessment');
  const output = success('render', a);
  assert.ok(output.includes(a.scope));
  assert.ok(output.includes(a.findings[0].action.replaceAll('.', '\\.')));
  assert.ok(output.includes(`<${a.evidence[0].url}>`));
  assert.ok(output.includes('**Preliminary**'));
  assert.ok(output.includes('**SYNTHETIC EXAMPLE'));
});

test('renderer treats embedded HTML and Markdown from documents as text', () => {
  const a = readExample('assessment');
  a.evidence[0].excerpt = '<script>alert(1)</script>\n[click](javascript:alert(1))';
  const output = success('render', a);
  assert.ok(!output.includes('<script>'));
  assert.ok(!output.includes('[click]('));
  assert.ok(output.includes('&lt;script&gt;'));
});

test('report uses readable missing information and omits absent optional platform site', () => {
  const a = assessment();
  a.brief.destinations[0].country = 'EU';
  a.findings = [];
  const output = success('render', a);
  assert.ok(output.includes('Specific EU destination countries'));
  assert.ok(!output.includes('destinations['));
  assert.ok(!output.includes('destinations\\['));
  assert.ok(output.includes('platforms: Shopify\n'));
  assert.ok(!output.includes('site unknown'));
});

test('usage errors are distinct from input failures', () => {
  const result = spawnSync(process.execPath, [cli, 'unknown'], { encoding: 'utf8' });
  assert.equal(result.status, 2);
  assert.equal(result.stdout, '');
});

test('help does not require an input file', () => {
  const result = spawnSync(process.execPath, [cli, '--help'], { encoding: 'utf8' });
  assert.equal(result.status, 0);
  assert.equal(result.stderr, '');
});
