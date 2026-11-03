export class ValidationError extends Error {
    problems;
    constructor(problems) {
        super(problems.join("\n"));
        this.problems = problems;
        this.name = "ValidationError";
    }
}
const countryCodes = new Set(("AD AE AF AG AI AL AM AO AQ AR AS AT AU AW AX AZ BA BB BD BE BF BG BH BI BJ BL BM BN BO BQ BR BS BT BV BW BY BZ CA CC CD CF CG CH CI CK CL CM CN CO CR CU CV CW CX CY CZ DE DJ DK DM DO DZ EC EE EG EH ER ES ET FI FJ FK FM FO FR GA GB GD GE GF GG GH GI GL GM GN GP GQ GR GS GT GU GW GY HK HM HN HR HT HU ID IE IL IM IN IO IQ IR IS IT JE JM JO JP KE KG KH KI KM KN KP KR KW KY KZ LA LB LC LI LK LR LS LT LU LV LY MA MC MD ME MF MG MH MK ML MM MN MO MP MQ MR MS MT MU MV MW MX MY MZ NA NC NE NF NG NI NL NO NP NR NU NZ OM PA PE PF PG PH PK PL PM PN PR PS PT PW PY QA RE RO RS RU RW SA SB SC SD SE SG SH SI SJ SK SL SM SN SO SR SS ST SV SX SY SZ TC TD TF TG TH TJ TK TL TM TN TO TR TT TV TW TZ UA UG UM US UY UZ VA VC VE VG VI VN VU WF WS YE YT ZA ZM ZW").split(" "));
const euMembers = new Set("AT BE BG HR CY CZ DE DK EE ES FI FR GR HU IE IT LT LU LV MT NL PL PT RO SE SI SK".split(" "));
const statuses = ["issue-found", "insufficient-evidence", "not-applicable", "not-checked", "no-issue-found"];
function object(value, path, keys, errors) {
    if (!value || typeof value !== "object" || Array.isArray(value)) {
        errors.push(`${path}: expected an object`);
        return {};
    }
    const result = value;
    for (const key of Object.keys(result)) {
        if (!keys.includes(key))
            errors.push(`${path}.${key}: unsupported field`);
    }
    return result;
}
function text(value, path, errors, optional = false) {
    if (value === undefined && optional)
        return false;
    if (typeof value !== "string" || !value.trim() || /[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/u.test(value)) {
        errors.push(`${path}: expected nonempty text without control characters`);
        return false;
    }
    return true;
}
function array(value, path, errors, optional = false) {
    if (value === undefined && optional)
        return [];
    if (!Array.isArray(value)) {
        errors.push(`${path}: expected an array`);
        return [];
    }
    return value;
}
function strings(value, path, errors, optional = false) {
    return array(value, path, errors, optional).filter((entry, i) => text(entry, `${path}[${i}]`, errors));
}
function date(value, path, errors, optional = false) {
    if (value === undefined && optional)
        return false;
    if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/u.test(value) || !Number.isFinite(Date.parse(value)) || new Date(value).toISOString().slice(0, 10) !== value) {
        errors.push(`${path}: expected a real calendar date in YYYY-MM-DD format`);
        return false;
    }
    return true;
}
function plannedDate(value, path, errors) {
    if (value === undefined)
        return false;
    if (typeof value === "string" && /^\d{4}-(0[1-9]|1[0-2])$/u.test(value))
        return true;
    const localErrors = [];
    if (date(value, path, localErrors))
        return true;
    errors.push(`${path}: expected a real calendar month YYYY-MM or date YYYY-MM-DD`);
    return false;
}
/** Month precision remains unchanged in the document; only comparisons use interval bounds. */
function plannedBoundary(value, edge) {
    if (!value || value.length === 10)
        return value;
    if (edge === "start")
        return `${value}-01`;
    const last = new Date(`${value}-01T00:00:00.000Z`);
    last.setUTCMonth(last.getUTCMonth() + 1, 0);
    return last.toISOString().slice(0, 10);
}
function choice(value, path, options, errors, optional = false) {
    if (value === undefined && optional)
        return;
    if (typeof value !== "string" || !options.includes(value))
        errors.push(`${path}: expected one of ${options.join(", ")}`);
}
function jurisdiction(value, path, errors, allowEu = true) {
    if (typeof value !== "string" || !(countryCodes.has(value) || (allowEu && value === "EU"))) {
        errors.push(`${path}: use an uppercase ISO 3166-1 alpha-2 country code${allowEu ? " or EU" : " (for example US, DE, GB)"}`);
    }
}
function unique(values, path, errors) {
    if (new Set(values).size !== values.length)
        errors.push(`${path}: duplicate values are not allowed`);
}
function checkBrief(value, path, errors) {
    const b = object(value, path, ["schemaVersion", "asOf", "product", "destinations", "plannedSale", "seller", "unknowns"], errors);
    if (b.schemaVersion !== 1)
        errors.push(`${path}.schemaVersion: expected 1`);
    date(b.asOf, `${path}.asOf`, errors);
    if (b.product !== undefined) {
        const p = object(b.product, `${path}.product`, ["name", "facts"], errors);
        text(p.name, `${path}.product.name`, errors, true);
        strings(p.facts, `${path}.product.facts`, errors, true);
    }
    array(b.destinations, `${path}.destinations`, errors, true).forEach((entry, i) => {
        const destPath = `${path}.destinations[${i}]`;
        const d = object(entry, destPath, ["country", "subdivision", "platforms"], errors);
        jurisdiction(d.country, `${destPath}.country`, errors);
        text(d.subdivision, `${destPath}.subdivision`, errors, true);
        array(d.platforms, `${destPath}.platforms`, errors, true).forEach((entry, j) => {
            const p = object(entry, `${destPath}.platforms[${j}]`, ["name", "site"], errors);
            text(p.name, `${destPath}.platforms[${j}].name`, errors);
            text(p.site, `${destPath}.platforms[${j}].site`, errors, true);
        });
    });
    if (b.plannedSale !== undefined) {
        const s = object(b.plannedSale, `${path}.plannedSale`, ["start", "end", "note"], errors);
        const startValid = plannedDate(s.start, `${path}.plannedSale.start`, errors);
        const endValid = plannedDate(s.end, `${path}.plannedSale.end`, errors);
        text(s.note, `${path}.plannedSale.note`, errors, true);
        if (startValid && endValid && plannedBoundary(s.end, "end") < plannedBoundary(s.start, "start"))
            errors.push(`${path}.plannedSale: end precedes start`);
    }
    if (b.seller !== undefined) {
        const s = object(b.seller, `${path}.seller`, ["location", "shipFrom", "fulfilment"], errors);
        for (const k of ["location", "shipFrom", "fulfilment"])
            text(s[k], `${path}.seller.${k}`, errors, true);
    }
    strings(b.unknowns, `${path}.unknowns`, errors, true);
}
export function parseBrief(value) {
    const errors = [];
    checkBrief(value, "brief", errors);
    if (errors.length)
        throw new ValidationError(errors);
    return value;
}
export function inspectBrief(brief) {
    const pending = [];
    const warnings = [];
    if (!brief.product?.name)
        pending.push({ field: "product.name", question: "你准备卖什么商品？" });
    if (!brief.destinations?.length)
        pending.push({ field: "destinations", question: "准备卖到哪个国家或地区？" });
    brief.destinations?.forEach((d, i) => {
        if (d.country === "EU") {
            pending.push({ field: `destinations[${i}].country`, question: "准备卖到欧盟的哪些国家？还没决定的话，可以先查欧盟共同要求。" });
            warnings.push("EU baseline research can begin; national requirements remain pending until destination countries are specified.");
        }
    });
    if (!brief.plannedSale?.start)
        pending.push({ field: "plannedSale.start", question: "大概什么时候开始销售？不确定也可以先说明。" });
    brief.destinations?.forEach((d, i) => {
        if (!d.platforms?.length)
            pending.push({ field: `destinations[${i}].platforms`, question: `准备通过哪个平台向 ${d.country} 销售？` });
        d.platforms?.forEach(p => {
            if (!p.site && /amazon|tiktok/iu.test(p.name))
                warnings.push(`${p.name}: confirm the marketplace site only if it is ambiguous in the user's supplied context; destination alone does not establish the site.`);
        });
        if (!new Set(["US", "DE", "EU"]).has(d.country))
            warnings.push(`${d.country}: outside the curated v1 US-federal / EU-with-Germany coverage; identify additional jurisdiction research explicitly.`);
    });
    if (!brief.seller?.fulfilment)
        warnings.push("Fulfilment is unknown; determine whether it changes the import, tax or responsible-party analysis.");
    if (brief.unknowns?.length)
        warnings.push("User-supplied unknowns remain unresolved.");
    return {
        preliminary: pending.length > 0 || Boolean(brief.unknowns?.length),
        readyToResearch: Boolean(brief.product?.name && brief.destinations?.length),
        missingCoreFields: pending.map(p => p.field),
        nextQuestions: pending.slice(0, 2),
        warnings,
    };
}
function covers(scope, country) {
    return scope === country || (scope === "EU" && euMembers.has(country));
}
export function parseAssessment(value) {
    const errors = [];
    const a = object(value, "assessment", ["schemaVersion", "brief", "scope", "evidence", "findings", "synthetic"], errors);
    if (a.schemaVersion !== 1)
        errors.push("assessment.schemaVersion: expected 1");
    checkBrief(a.brief, "assessment.brief", errors);
    text(a.scope, "assessment.scope", errors);
    if (a.synthetic !== undefined && typeof a.synthetic !== "boolean")
        errors.push("assessment.synthetic: expected boolean");
    const evidence = array(a.evidence, "assessment.evidence", errors);
    evidence.forEach((entry, i) => {
        const p = `assessment.evidence[${i}]`;
        const e = object(entry, p, ["id", "title", "url", "authority", "jurisdictions", "accessedAt", "excerpt", "inspected"], errors);
        for (const key of ["id", "title", "excerpt"])
            text(e[key], `${p}.${key}`, errors);
        if (text(e.url, `${p}.url`, errors)) {
            try {
                const url = new URL(e.url);
                if (!["http:", "https:"].includes(url.protocol) || url.username || url.password)
                    throw new Error();
            }
            catch {
                errors.push(`${p}.url: expected an HTTP(S) source URL without credentials`);
            }
        }
        choice(e.authority, `${p}.authority`, ["regulator", "legislation", "platform", "other"], errors);
        const j = strings(e.jurisdictions, `${p}.jurisdictions`, errors);
        if (!j.length)
            errors.push(`${p}.jurisdictions: declare at least one jurisdiction`);
        j.forEach((v, k) => jurisdiction(v, `${p}.jurisdictions[${k}]`, errors));
        unique(j, `${p}.jurisdictions`, errors);
        date(e.accessedAt, `${p}.accessedAt`, errors);
        if (typeof e.inspected !== "boolean")
            errors.push(`${p}.inspected: expected boolean`);
    });
    const findings = array(a.findings, "assessment.findings", errors);
    findings.forEach((entry, i) => {
        const p = `assessment.findings[${i}]`;
        const f = object(entry, p, ["id", "title", "scope", "status", "kind", "jurisdiction", "sourceIds", "explanation", "action", "applicability"], errors);
        for (const k of ["id", "title", "scope", "explanation", "action"])
            text(f[k], `${p}.${k}`, errors);
        choice(f.status, `${p}.status`, statuses, errors);
        choice(f.kind, `${p}.kind`, ["law", "platform-policy", "guidance"], errors);
        jurisdiction(f.jurisdiction, `${p}.jurisdiction`, errors);
        unique(strings(f.sourceIds, `${p}.sourceIds`, errors), `${p}.sourceIds`, errors);
        const ap = object(f.applicability, `${p}.applicability`, ["reason", "temporalStatus", "effectiveFrom", "effectiveTo", "ruleStatus"], errors);
        text(ap.reason, `${p}.applicability.reason`, errors);
        choice(ap.temporalStatus, `${p}.applicability.temporalStatus`, ["applies", "uncertain", "outside-period"], errors);
        choice(ap.ruleStatus, `${p}.applicability.ruleStatus`, ["enacted", "proposed", "unknown"], errors, true);
        const from = date(ap.effectiveFrom, `${p}.applicability.effectiveFrom`, errors, true);
        const to = date(ap.effectiveTo, `${p}.applicability.effectiveTo`, errors, true);
        if (from && to && ap.effectiveTo < ap.effectiveFrom)
            errors.push(`${p}.applicability: effectiveTo precedes effectiveFrom`);
    });
    if (errors.length)
        throw new ValidationError(errors);
    const parsed = value;
    unique(parsed.evidence.map(e => e.id), "assessment.evidence ids", errors);
    unique(parsed.findings.map(f => f.id), "assessment.findings ids", errors);
    const sources = new Map(parsed.evidence.map(e => [e.id, e]));
    for (const e of parsed.evidence) {
        if (e.accessedAt > parsed.brief.asOf)
            errors.push(`evidence ${e.id}: accessedAt is after brief.asOf`);
    }
    const destinations = parsed.brief.destinations ?? [];
    for (const f of parsed.findings) {
        const prefix = `finding ${f.id}`;
        const ap = f.applicability;
        const substantive = ["issue-found", "no-issue-found", "not-applicable"].includes(f.status);
        if (!destinations.some(d => covers(f.jurisdiction, d.country)))
            errors.push(`${prefix}: jurisdiction has no matching destination in the brief`);
        const used = f.sourceIds.flatMap(id => {
            const source = sources.get(id);
            if (!source) {
                errors.push(`${prefix}: source ${id} does not exist`);
                return [];
            }
            if (!source.jurisdictions.some(j => covers(j, f.jurisdiction)))
                errors.push(`${prefix}: source ${id} does not cover the finding's jurisdiction`);
            return [source];
        });
        if (substantive) {
            const authoritative = used.some(e => e.inspected && (f.kind === "platform-policy" ? e.authority === "platform" : f.kind === "law" ? ["legislation", "regulator"].includes(e.authority) : e.authority !== "other"));
            if (!authoritative)
                errors.push(`${prefix}: substantive conclusions require inspected authoritative source support matching the finding kind`);
            if (used.some(e => !e.inspected))
                errors.push(`${prefix}: uninspected sources cannot support a substantive conclusion`);
            if (f.kind === "law" && ap.ruleStatus !== "enacted")
                errors.push(`${prefix}: legal conclusions require ruleStatus enacted; proposals/unknown rules belong in uncertain guidance or insufficient-evidence findings`);
        }
        if (["issue-found", "no-issue-found"].includes(f.status) && ap.temporalStatus !== "applies")
            errors.push(`${prefix}: issue-found/no-issue-found requires temporalStatus applies`);
        if (ap.ruleStatus === "proposed" && ap.temporalStatus !== "uncertain")
            errors.push(`${prefix}: proposed rules must have uncertain temporal applicability`);
        const start = plannedBoundary(parsed.brief.plannedSale?.start, "start");
        const end = plannedBoundary(parsed.brief.plannedSale?.end, "end");
        if (ap.temporalStatus === "applies" && !start && ap.effectiveFrom && ap.effectiveFrom > parsed.brief.asOf)
            errors.push(`${prefix}: future applicability requires a known selling start or uncertain temporalStatus`);
        const disjoint = Boolean((start && ap.effectiveTo && ap.effectiveTo < start) || (end && ap.effectiveFrom && ap.effectiveFrom > end));
        if (disjoint && ap.temporalStatus === "applies")
            errors.push(`${prefix}: declared effective period does not overlap the planned selling period`);
        if (ap.temporalStatus === "outside-period" && !disjoint)
            errors.push(`${prefix}: outside-period requires a demonstrably disjoint selling/effective boundary; use uncertain when dates do not establish exclusion`);
    }
    if (errors.length)
        throw new ValidationError(errors);
    return parsed;
}
export function assessmentSummary(assessment) {
    const intake = inspectBrief(assessment.brief);
    const warnings = [...intake.warnings];
    if (!assessment.findings.length)
        warnings.push("No findings were supplied; coverage is unchecked, not safe or compliant.");
    if (assessment.findings.some(f => ["not-checked", "insufficient-evidence"].includes(f.status)))
        warnings.push("Some findings remain unverified or lack evidence.");
    if (assessment.synthetic)
        warnings.push("Synthetic example only; not a live assessment.");
    return {
        valid: true,
        preliminary: intake.preliminary || !assessment.findings.length || assessment.findings.some(f => ["not-checked", "insufficient-evidence"].includes(f.status)),
        coverage: assessment.findings.length ? "partial" : "unchecked",
        findings: assessment.findings.length,
        inspectedSources: assessment.evidence.filter(e => e.inspected).length,
        missingCoreFields: intake.missingCoreFields,
        warnings,
    };
}
