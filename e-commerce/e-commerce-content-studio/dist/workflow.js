import { createHash } from "node:crypto";
import { PLACEMENTS, PLATFORMS } from "./types.js";
const FRESHNESS_DAYS = 7;
function fail(message) { throw new Error(message); }
function object(value, at) {
    if (!value || typeof value !== "object" || Array.isArray(value))
        fail(`${at} must be an object.`);
    return value;
}
function text(value, at) {
    if (typeof value !== "string" || !value.trim())
        fail(`${at} must be a non-empty string.`);
    return value;
}
function number(value, at, minimum = 0) {
    if (typeof value !== "number" || !Number.isFinite(value) || value < minimum)
        fail(`${at} must be a finite number >= ${minimum}.`);
    return value;
}
function integer(value, at, minimum = 1) {
    const result = number(value, at, minimum);
    if (!Number.isSafeInteger(result))
        fail(`${at} must be an integer.`);
    return result;
}
function array(value, at, minimum = 1) {
    if (!Array.isArray(value) || value.length < minimum)
        fail(`${at} must be an array with at least ${minimum} item(s).`);
    return value;
}
function strings(value, at, minimum = 1) {
    const result = array(value, at, minimum).map((item, i) => text(item, `${at}[${i}]`));
    unique(result, at);
    return result;
}
function unique(values, at) {
    if (new Set(values).size !== values.length)
        fail(`${at} contains duplicate values.`);
}
function oneOf(value, allowed, at) {
    if (typeof value !== "string" || !allowed.includes(value))
        fail(`${at} must be one of: ${allowed.join(", ")}.`);
    return value;
}
function url(value, at) {
    const input = text(value, at);
    let parsed;
    try {
        parsed = new URL(input);
    }
    catch {
        return fail(`${at} must be an absolute HTTPS or HTTP URL.`);
    }
    if (!["https:", "http:"].includes(parsed.protocol) || parsed.username || parsed.password)
        fail(`${at} must be an absolute HTTPS or HTTP URL without credentials.`);
    return input;
}
function date(value, at) {
    const input = text(value, at);
    if (!/^\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?Z)?$/.test(input) || Number.isNaN(Date.parse(input)))
        fail(`${at} must be a UTC ISO date or timestamp.`);
    if (new Date(input).toISOString().slice(0, 10) !== input.slice(0, 10))
        fail(`${at} is not a real calendar date.`);
    return input;
}
function nullableText(value, at) { return value === null ? null : text(value, at); }
function platform(value, at) { return oneOf(value, PLATFORMS, at); }
function placement(value, selectedPlatform, at) {
    const result = oneOf(value, Object.keys(PLACEMENTS), at);
    if (PLACEMENTS[result].platform !== selectedPlatform)
        fail(`${at} does not belong to ${selectedPlatform}.`);
    return result;
}
function copy(value) { return structuredClone(value); }
function hasTarget(brief, selectedPlatform, selectedPlacement) {
    return brief.targets.some(target => target.platform === selectedPlatform && target.placements.includes(selectedPlacement));
}
export function validateBrief(value) {
    const brief = object(value, "brief");
    text(brief.name, "brief.name");
    text(brief.goal, "brief.goal");
    const targets = array(brief.targets, "brief.targets").map((item, i) => {
        const target = object(item, `brief.targets[${i}]`);
        const selectedPlatform = platform(target.platform, "target.platform");
        const market = text(target.market, "target.market");
        if (selectedPlatform !== "shopify" && market !== "US")
            fail(`${selectedPlatform} currently supports the US market only.`);
        text(target.language, "target.language");
        const placements = array(target.placements, "target.placements").map(value => placement(value, selectedPlatform, "target.placements"));
        unique(placements, "target.placements");
        if (target.themeUrl !== undefined) {
            if (selectedPlatform !== "shopify")
                fail("themeUrl is only supported for Shopify.");
            url(target.themeUrl, "target.themeUrl");
        }
        if (target.themeDescription !== undefined) {
            if (selectedPlatform !== "shopify")
                fail("themeDescription is only supported for Shopify.");
            text(target.themeDescription, "target.themeDescription");
        }
        if (selectedPlatform === "shopify" && target.themeUrl === undefined && target.themeDescription === undefined)
            fail("Shopify requires themeUrl or themeDescription so research can identify store-specific media requirements.");
        return selectedPlatform;
    });
    unique(targets, "brief.targets platforms (use a separate project per market)");
    const referenceInputs = array(brief.references, "brief.references: user product photos are required").map((item, i) => {
        const ref = object(item, `brief.references[${i}]`);
        text(ref.id, "reference.id");
        text(ref.sku, "reference.sku");
        text(ref.path, "reference.path");
        if (!/^[A-Za-z0-9_-]+$/.test(ref.id))
            fail("Reference ids may contain only letters, digits, underscores, or hyphens.");
        oneOf(ref.source, ["user-product-photo"], "reference.source");
        if (ref.remoteUrl !== undefined) {
            const remoteUrl = url(ref.remoteUrl, "reference.remoteUrl");
            if (new URL(remoteUrl).protocol !== "https:")
                fail("reference.remoteUrl must use HTTPS and point to the same supplied product photo.");
        }
        return ref;
    });
    unique(referenceInputs.map(ref => ref.id), "brief.references ids");
    const factIds = [];
    const skus = array(brief.products, "brief.products").map((item, i) => {
        const product = object(item, `brief.products[${i}]`);
        const sku = text(product.sku, "product.sku");
        text(product.name, "product.name");
        text(product.category, "product.category");
        if (!referenceInputs.some(ref => ref.sku === sku))
            fail(`Product ${sku} requires at least one user product photo. Do not research or generate before supplying it.`);
        for (const item of array(product.facts, "product.facts", 0)) {
            const fact = object(item, "product.fact");
            factIds.push(text(fact.id, "fact.id"));
            text(fact.text, "fact.text");
            const source = object(fact.source, "fact.source");
            const kind = oneOf(source.kind, ["user-confirmed", "visible-in-reference", "document"], "fact.source.kind");
            if (kind === "visible-in-reference") {
                const referenceId = text(source.referenceId, "fact.source.referenceId");
                if (!referenceInputs.some(ref => ref.id === referenceId && ref.sku === sku))
                    fail(`Fact ${fact.id} must cite a reference for its own SKU.`);
            }
            else if (kind === "document")
                url(source.url, "fact.source.url");
            else
                text(source.note, "fact.source.note (record the user's confirmation)");
        }
        return sku;
    });
    unique(skus, "brief.products SKUs");
    unique(factIds, "product fact ids");
    for (const ref of referenceInputs)
        if (!skus.includes(ref.sku))
            fail(`Reference ${ref.id} has an unknown SKU.`);
    const budget = object(brief.budget, "brief.budget");
    oneOf(budget.currency, ["USD"], "brief.budget.currency");
    number(budget.maxEstimatedCostUsd, "brief.budget.maxEstimatedCostUsd", 0.000001);
    integer(budget.maxAttemptsPerDeliverable, "brief.budget.maxAttemptsPerDeliverable");
    return copy(brief);
}
function validateReferences(value, brief) {
    const refs = array(value, "references: validated user product photos are required").map((item, i) => {
        const ref = object(item, `references[${i}]`);
        const input = brief.references.find(input => input.id === ref.id);
        if (!input || input.sku !== ref.sku || input.path !== ref.path || input.remoteUrl !== ref.remoteUrl || ref.source !== "user-product-photo")
            fail(`Validated reference ${ref.id} must match the brief reference exactly.`);
        if (typeof ref.sha256 !== "string" || !/^[a-f0-9]{64}$/.test(ref.sha256))
            fail("reference.sha256 must be a lowercase SHA-256 digest from inspected image bytes.");
        oneOf(ref.mimeType, ["image/png", "image/jpeg", "image/webp"], "reference.mimeType");
        integer(ref.width, "reference.width");
        integer(ref.height, "reference.height");
        return ref;
    });
    unique(refs.map(ref => ref.id), "validated reference ids");
    if (refs.length !== brief.references.length || brief.references.some(input => !refs.some(ref => ref.id === input.id)))
        fail("Every product photo in the brief must be inspected before continuing.");
    return copy(refs);
}
export function validateResearch(value, brief) {
    const research = object(value, "research");
    text(research.scope, "research.scope");
    const ruleIds = [];
    const rulePairs = new Set();
    const mandatoryPairs = new Set();
    for (const item of array(research.rules, "research.rules")) {
        const rule = object(item, "research.rule");
        ruleIds.push(text(rule.id, "rule.id"));
        const selectedPlatform = platform(rule.platform, "rule.platform");
        const selectedPlacement = placement(rule.placement, selectedPlatform, "rule.placement");
        if (!hasTarget(brief, selectedPlatform, selectedPlacement))
            fail(`Rule ${rule.id} is outside the selected platforms and placements.`);
        rulePairs.add(`${selectedPlatform}/${selectedPlacement}`);
        text(rule.requirement, "rule.requirement");
        oneOf(rule.status, ["mandatory", "recommended"], "rule.status");
        if (rule.status === "mandatory")
            mandatoryPairs.add(`${selectedPlatform}/${selectedPlacement}`);
        url(rule.sourceUrl, "rule.sourceUrl");
        text(rule.publisher, "rule.publisher");
        date(rule.fetchedAt, "rule.fetchedAt");
        if (rule.effectiveAt !== null)
            date(rule.effectiveAt, "rule.effectiveAt (use null when unknown)");
        nullableText(rule.conflict, "rule.conflict (use null when no unresolved conflict exists)");
    }
    unique(ruleIds, "research rule ids");
    for (const target of brief.targets)
        for (const selectedPlacement of target.placements) {
            if (!rulePairs.has(`${target.platform}/${selectedPlacement}`))
                fail(`Research is missing requirements for ${target.platform}/${selectedPlacement}.`);
            if (!mandatoryPairs.has(`${target.platform}/${selectedPlacement}`))
                fail(`Research must identify mandatory requirements for ${target.platform}/${selectedPlacement}.`);
        }
    const exampleIds = [];
    const examplePlatforms = new Set();
    for (const item of array(research.examples, "research.examples", 0)) {
        const example = object(item, "research.example");
        exampleIds.push(text(example.id, "example.id"));
        const selectedPlatform = platform(example.platform, "example.platform");
        const selectedPlacement = placement(example.placement, selectedPlatform, "example.placement");
        if (!hasTarget(brief, selectedPlatform, selectedPlacement))
            fail(`Example ${example.id} is outside the selected platforms and placements.`);
        examplePlatforms.add(selectedPlatform);
        url(example.url, "example.url");
        date(example.observedAt, "example.observedAt");
        const tier = oneOf(example.metricTier, ["measured", "platform-selected", "proxy"], "example.metricTier");
        for (const item of array(example.metrics, "example.metrics (record null for unknown results)")) {
            const metric = object(item, "example.metric");
            text(metric.name, "metric.name");
            if (metric.value !== null && typeof metric.value !== "number")
                text(metric.value, "metric.value (use null for unknown)");
            if (typeof metric.value === "number")
                number(metric.value, "metric.value", -Number.MAX_VALUE);
            nullableText(metric.window, "metric.window (use null for unknown)");
            if (tier === "measured" && (metric.value === null || metric.window === null))
                fail("Measured performance requires an actual metric value and measurement window; use a proxy or platform-selected label otherwise.");
        }
        strings(example.takeaways, "example.takeaways");
    }
    unique(exampleIds, "research example ids");
    const limitedPlatforms = new Set();
    if (research.exampleLimitations !== undefined)
        for (const item of array(research.exampleLimitations, "research.exampleLimitations", 0)) {
            const limitation = object(item, "research.exampleLimitation");
            const selectedPlatform = platform(limitation.platform, "exampleLimitation.platform");
            if (!brief.targets.some(target => target.platform === selectedPlatform))
                fail("An example limitation must apply to a selected platform.");
            text(limitation.reason, "exampleLimitation.reason");
            limitedPlatforms.add(selectedPlatform);
        }
    for (const target of brief.targets)
        if (!examplePlatforms.has(target.platform) && !limitedPlatforms.has(target.platform))
            fail(`No comparable content evidence for ${target.platform}: record an explicit exampleLimitations reason instead of inventing performance evidence.`);
    strings(research.synthesis, "research.synthesis");
    strings(research.limitations, "research.limitations");
    return copy(research);
}
function assertResearchUsable(research, now) {
    const timestamp = Date.parse(date(now, "now"));
    for (const rule of research.rules) {
        if (rule.conflict !== null)
            fail(`Resolve research conflict ${rule.id} before approving or generating: ${rule.conflict}`);
        const age = (timestamp - Date.parse(rule.fetchedAt)) / 86_400_000;
        if (age > FRESHNESS_DAYS)
            fail(`Research rule ${rule.id} is older than ${FRESHNESS_DAYS} days; refresh the official requirement and reapprove the playbook.`);
        if (age < -1)
            fail(`Research rule ${rule.id} has a future fetchedAt date.`);
    }
}
export function validatePlaybook(value, brief, research) {
    const playbook = object(value, "playbook");
    for (const key of ["title", "version", "summary", "creativeDirection"])
        text(playbook[key], `playbook.${key}`);
    const ids = [];
    let estimatedTotal = 0;
    for (const item of array(playbook.deliverables, "playbook.deliverables")) {
        const deliverable = object(item, "deliverable");
        const id = text(deliverable.id, "deliverable.id");
        if (!/^[A-Za-z0-9][A-Za-z0-9_-]{0,99}$/.test(id))
            fail("Deliverable ids must be safe file identifiers: letters, digits, underscores, or hyphens, beginning with a letter or digit (maximum 100 characters).");
        ids.push(id);
        const sku = text(deliverable.sku, "deliverable.sku");
        const product = brief.products.find(product => product.sku === sku);
        if (!product)
            fail(`Deliverable ${deliverable.id} has an unknown SKU.`);
        const selectedPlatform = platform(deliverable.platform, "deliverable.platform");
        const selectedPlacement = placement(deliverable.placement, selectedPlatform, "deliverable.placement");
        if (!hasTarget(brief, selectedPlatform, selectedPlacement))
            fail(`Deliverable ${deliverable.id} is outside the selected platforms and placements.`);
        const kind = oneOf(deliverable.kind, ["image", "copy", "video"], "deliverable.kind");
        if (PLACEMENTS[selectedPlacement].kind !== kind)
            fail(`Deliverable ${deliverable.id} kind does not match its placement.`);
        for (const referenceId of strings(deliverable.referenceIds, "deliverable.referenceIds")) {
            if (!brief.references.some(ref => ref.id === referenceId && ref.sku === sku))
                fail(`Deliverable ${deliverable.id} must cite photos of its own SKU.`);
        }
        for (const claimId of strings(deliverable.claimIds, "deliverable.claimIds", 0)) {
            if (!product.facts.some(fact => fact.id === claimId))
                fail(`Deliverable ${deliverable.id} cites an unsupported product claim: ${claimId}.`);
        }
        const ruleIds = strings(deliverable.ruleIds, "deliverable.ruleIds");
        for (const ruleId of ruleIds) {
            if (!research.rules.some(rule => rule.id === ruleId && rule.platform === selectedPlatform && rule.placement === selectedPlacement))
                fail(`Deliverable ${deliverable.id} cites a rule from another placement or an unknown rule.`);
        }
        for (const rule of research.rules.filter(rule => rule.platform === selectedPlatform && rule.placement === selectedPlacement && rule.status === "mandatory")) {
            if (!ruleIds.includes(rule.id))
                fail(`Deliverable ${deliverable.id} must include mandatory rule ${rule.id}.`);
        }
        text(deliverable.prompt, "deliverable.prompt");
        text(deliverable.model, "deliverable.model");
        if (kind === "image") {
            const imageMode = oneOf(deliverable.imageMode, ["preserve", "edit"], "deliverable.imageMode");
            if (imageMode === "preserve" && deliverable.model !== "local-photo-export")
                fail("Preserve mode requires model local-photo-export; it retains the actual product photo pixels.");
            if (imageMode === "edit" && deliverable.model === "local-photo-export")
                fail("Image edit mode requires a verified reference-aware generation model.");
            if (selectedPlacement === "amazon-main" && imageMode !== "preserve")
                fail("Amazon main images require preserve mode in 1.0.0. Supply a compliant product photograph.");
        }
        if (kind !== "copy") {
            if (typeof deliverable.size !== "string" || !/^[1-9]\d{0,4}x[1-9]\d{0,4}$/.test(deliverable.size))
                fail("Image/video deliverable.size must be explicit WIDTHxHEIGHT pixels.");
        }
        if (kind === "image" && deliverable.imageMode === "edit")
            oneOf(deliverable.imageSize, ["1K", "2K", "4K"], "deliverable.imageSize (include the source resolution in the approved pricing estimate)");
        if (kind === "video") {
            number(deliverable.durationSeconds, "deliverable.durationSeconds", 0.001);
            if (deliverable.allowExperimentalVideo !== true)
                fail("The current Wan video adapter is experimental and its gateway contract is not live-verified. Set allowExperimentalVideo only when this is disclosed in the proposed playbook for explicit user approval.");
        }
        if (kind === "copy") {
            const limits = object(deliverable.copyLimits, "deliverable.copyLimits");
            if (!Object.keys(limits).length)
                fail("Copy deliverables require explicit field character limits.");
            for (const [field, limit] of Object.entries(limits)) {
                text(field, "copyLimits field");
                integer(limit, `copyLimits.${field}`);
            }
        }
        if (deliverable.constraints !== undefined) {
            const constraints = object(deliverable.constraints, "deliverable.constraints");
            if (kind === "copy" && Object.keys(constraints).length)
                fail("Copy deliverables use copyLimits rather than media constraints.");
            const allowed = ["minWidth", "minHeight", "maxBytes", "maxDurationSeconds", "aspectRatio"];
            for (const key of Object.keys(constraints))
                if (!allowed.includes(key))
                    fail(`Unsupported media constraint ${key}.`);
            for (const key of ["minWidth", "minHeight", "maxBytes"])
                if (constraints[key] !== undefined)
                    integer(constraints[key], `constraints.${key}`);
            if (constraints.maxDurationSeconds !== undefined) {
                if (kind !== "video")
                    fail("maxDurationSeconds applies only to video.");
                number(constraints.maxDurationSeconds, "constraints.maxDurationSeconds", 0.001);
                if (deliverable.durationSeconds > constraints.maxDurationSeconds)
                    fail("Planned video duration exceeds the researched maximum.");
            }
            if (constraints.aspectRatio !== undefined && (typeof constraints.aspectRatio !== "string" || !/^[1-9]\d{0,4}:[1-9]\d{0,4}$/.test(constraints.aspectRatio)))
                fail("constraints.aspectRatio must be WIDTH:HEIGHT.");
            if (typeof deliverable.size === "string") {
                const [width, height] = deliverable.size.split("x").map(Number);
                if (constraints.minWidth !== undefined && width < constraints.minWidth)
                    fail("Planned width is below the researched minimum.");
                if (constraints.minHeight !== undefined && height < constraints.minHeight)
                    fail("Planned height is below the researched minimum.");
                if (typeof constraints.aspectRatio === "string") {
                    const [ratioWidth, ratioHeight] = constraints.aspectRatio.split(":").map(Number);
                    if (Math.abs(width / height - ratioWidth / ratioHeight) > 0.001)
                        fail("Planned dimensions do not match the researched aspect ratio.");
                }
            }
        }
        const estimate = number(deliverable.estimatedCostUsd, "deliverable.estimatedCostUsd");
        if (deliverable.model === "local-photo-export") {
            if (estimate !== 0)
                fail("Local photo export has no AIsa generation cost; set estimatedCostUsd to 0.");
        }
        else {
            number(deliverable.estimatedCostUsd, "deliverable.estimatedCostUsd for paid generation", 0.000001);
            text(deliverable.pricingSource, "deliverable.pricingSource");
            date(deliverable.pricingCheckedAt, "deliverable.pricingCheckedAt");
        }
        estimatedTotal += estimate;
        strings(deliverable.successCriteria, "deliverable.successCriteria");
    }
    unique(ids, "playbook deliverable ids");
    const budget = object(playbook.budget, "playbook.budget");
    const estimate = number(budget.estimatedTotalUsd, "playbook.budget.estimatedTotalUsd");
    if (Math.abs(estimate - estimatedTotal) > 0.000001)
        fail("Playbook total estimate must equal the sum of deliverable estimates.");
    if (estimate > brief.budget.maxEstimatedCostUsd)
        fail("Playbook estimated cost exceeds the user's maximum estimated budget.");
    const attempts = integer(budget.maxAttemptsPerDeliverable, "playbook.budget.maxAttemptsPerDeliverable");
    if (attempts > brief.budget.maxAttemptsPerDeliverable)
        fail("Playbook attempt limit exceeds the brief's approved planning limit.");
    if (estimate * attempts > brief.budget.maxEstimatedCostUsd)
        fail("The estimate including all allowed attempts exceeds the user's maximum estimated budget. Reduce scope or attempts.");
    oneOf(budget.costControl, ["estimate-only"], "playbook.budget.costControl");
    strings(playbook.approvalNotes, "playbook.approvalNotes");
    return copy(playbook);
}
export function initProject(briefValue, references, now = new Date().toISOString()) {
    const brief = validateBrief(briefValue);
    date(now, "now");
    return { schemaVersion: 1, brief, references: validateReferences(references, brief), createdAt: now, updatedAt: now };
}
export function validateProject(value) {
    const input = object(value, "project");
    if (input.schemaVersion !== 1)
        fail("Unsupported project schema version.");
    const brief = validateBrief(input.brief);
    const references = validateReferences(input.references, brief);
    const state = { schemaVersion: 1, brief, references, createdAt: date(input.createdAt, "project.createdAt"), updatedAt: date(input.updatedAt, "project.updatedAt") };
    if (input.research !== undefined)
        state.research = validateResearch(input.research, brief);
    if (input.playbook !== undefined) {
        if (!state.research)
            fail("A playbook requires completed research.");
        state.playbook = validatePlaybook(input.playbook, brief, state.research);
    }
    if (input.approval !== undefined) {
        const approval = object(input.approval, "approval");
        if (!state.playbook)
            fail("Approval requires a playbook.");
        oneOf(approval.actor, ["user"], "approval.actor");
        text(approval.message, "approval.message");
        if (typeof approval.playbookHash !== "string" || !/^[a-f0-9]{64}$/.test(approval.playbookHash))
            fail("Approval requires an exact playbook hash.");
        date(approval.approvedAt, "approval.approvedAt");
        state.approval = copy(approval);
    }
    return state;
}
export function setResearch(stateValue, value, now = new Date().toISOString()) {
    const state = validateProject(stateValue);
    state.research = validateResearch(value, state.brief);
    delete state.playbook;
    delete state.approval;
    state.updatedAt = date(now, "now");
    return state;
}
export function setPlaybook(stateValue, value, now = new Date().toISOString()) {
    const state = validateProject(stateValue);
    if (!state.research)
        fail("Research and its report are required before preparing the playbook.");
    assertResearchUsable(state.research, now);
    state.playbook = validatePlaybook(value, state.brief, state.research);
    delete state.approval;
    state.updatedAt = date(now, "now");
    return state;
}
function canonical(value) {
    if (Array.isArray(value))
        return `[${value.map(canonical).join(",")}]`;
    if (value && typeof value === "object")
        return `{${Object.entries(value).filter(([, value]) => value !== undefined).sort(([a], [b]) => a.localeCompare(b)).map(([key, value]) => `${JSON.stringify(key)}:${canonical(value)}`).join(",")}}`;
    return JSON.stringify(value);
}
export function approvalHash(stateValue) {
    const state = validateProject(stateValue);
    if (!state.research || !state.playbook)
        fail("Research and a playbook are required to calculate an approval hash.");
    return createHash("sha256").update(canonical({ schemaVersion: state.schemaVersion, brief: state.brief, references: state.references, research: state.research, playbook: state.playbook })).digest("hex");
}
export function approvePlaybook(stateValue, evidence, now = new Date().toISOString()) {
    const state = validateProject(stateValue);
    if (!state.research || !state.playbook)
        fail("Present the research report and concrete playbook before asking for user approval.");
    assertResearchUsable(state.research, now);
    assertPricingCurrent(state.playbook, now);
    const input = object(evidence, "approval evidence");
    oneOf(input.actor, ["user"], "approval.actor");
    text(input.message, "approval.message: quote the user's explicit approval of this playbook");
    if (["true", "false"].includes(input.message.trim().toLowerCase()))
        fail("A boolean string is not an explicit user approval message.");
    const hash = approvalHash(state);
    if (input.playbookHash !== hash)
        fail("Approval hash does not match the current playbook, references, brief, and research. Present the current version to the user.");
    state.approval = { actor: "user", message: input.message, playbookHash: hash, approvedAt: date(now, "now") };
    state.updatedAt = now;
    return state;
}
export function assertReady(stateValue, now = new Date().toISOString()) {
    const state = validateProject(stateValue);
    if (!state.research || !state.playbook || !state.approval)
        fail("Generation requires current research, a concrete playbook, and explicit user approval of that exact playbook.");
    assertResearchUsable(state.research, now);
    assertPricingCurrent(state.playbook, now);
    if (state.approval.playbookHash !== approvalHash(state))
        fail("The approved brief, references, research, or playbook changed. Ask the user to approve the updated playbook before generating.");
    return copy(state.playbook);
}
function assertPricingCurrent(playbook, now) {
    for (const deliverable of playbook.deliverables) {
        if (deliverable.model === "local-photo-export")
            continue;
        const age = (Date.parse(now) - Date.parse(deliverable.pricingCheckedAt)) / 86_400_000;
        if (age > FRESHNESS_DAYS || age < -1)
            fail(`Pricing evidence for ${deliverable.id} must be checked within the past ${FRESHNESS_DAYS} days before approval or generation.`);
    }
}
function escape(value) { return value.replaceAll("|", "\\|").replaceAll("\n", " "); }
export function renderResearch(stateValue) {
    const state = validateProject(stateValue);
    if (!state.research)
        fail("No research report is available.");
    const research = state.research;
    const lines = [`# ${state.brief.name}: research report`, "", research.scope, "", "Evidence describes observed patterns and does not establish that the creative caused sales or conversion. Unknown metrics and time windows remain unknown.", "", "## Selected platforms and markets", ""];
    for (const target of state.brief.targets)
        lines.push(`- ${target.platform} / ${target.market} / ${target.language}: ${target.placements.join(", ")}${target.themeUrl ? `; theme/store: ${target.themeUrl}` : ""}${target.themeDescription ? `; theme description: ${target.themeDescription}` : ""}`);
    lines.push("", "Product scope:", "", ...state.brief.products.map(product => `- ${product.sku}: ${product.name}; category: ${product.category}`));
    lines.push("", "## Current requirements", "", "| Placement | Requirement | Status | Source | Fetched / effective | Unresolved conflict |", "| --- | --- | --- | --- | --- | --- |");
    for (const rule of research.rules)
        lines.push(`| ${rule.placement} (${escape(rule.id)}) | ${escape(rule.requirement)} | ${rule.status} | [${escape(rule.publisher)}](${rule.sourceUrl}) | ${rule.fetchedAt} / ${rule.effectiveAt ?? "unknown"} | ${escape(rule.conflict ?? "none")} |`);
    lines.push("", "## Comparable content and performance evidence", "");
    for (const example of research.examples) {
        lines.push(`### ${example.id}: ${example.platform} / ${example.placement}`, "", `[View example](${example.url}) · observed ${example.observedAt} · evidence tier: **${example.metricTier}**`, "");
        for (const metric of example.metrics)
            lines.push(`- ${metric.name}: ${metric.value ?? "unknown"}; measurement window: ${metric.window ?? "unknown"}`);
        lines.push("", ...example.takeaways.map(takeaway => `- ${takeaway}`), "");
    }
    lines.push("## Playbook implications", "", ...research.synthesis.map(item => `- ${item}`), "", "## Limitations", "", ...research.limitations.map(item => `- ${item}`), "", `Requirements must be refreshed after ${FRESHNESS_DAYS} days. Resolve every recorded conflict before approval or production.`, "");
    for (const limitation of research.exampleLimitations ?? [])
        lines.push(`- ${limitation.platform}: comparable content evidence unavailable — ${limitation.reason}`);
    return lines.join("\n");
}
export function renderPlaybook(stateValue) {
    const state = validateProject(stateValue);
    if (!state.playbook)
        fail("No playbook is available.");
    const playbook = state.playbook;
    const lines = [`# ${playbook.title} (${playbook.version})`, "", playbook.summary, "", "## Creative direction", "", playbook.creativeDirection, "", "## Planned deliverables", ""];
    for (const deliverable of playbook.deliverables) {
        lines.push(`### ${deliverable.id}: ${deliverable.platform} / ${deliverable.placement}`, "", `SKU: ${deliverable.sku} · kind: ${deliverable.kind} · model: ${deliverable.model}`, "", `References: ${deliverable.referenceIds.join(", ")} · supported claims: ${deliverable.claimIds.join(", ") || "none"} · rules: ${deliverable.ruleIds.join(", ")}`, "");
        if (deliverable.size)
            lines.push(`Dimensions: ${deliverable.size} pixels.`);
        if (deliverable.durationSeconds)
            lines.push(`Duration: ${deliverable.durationSeconds} seconds.`);
        if (deliverable.copyLimits)
            lines.push(`Copy character limits: ${Object.entries(deliverable.copyLimits).map(([field, limit]) => `${field}: ${limit}`).join("; ")}.`);
        if (deliverable.imageMode)
            lines.push(`Image mode: ${deliverable.imageMode}.`);
        if (deliverable.imageSize)
            lines.push(`Requested native source resolution: ${deliverable.imageSize}; its price must be included in the estimate. Original results are saved; exports may be fitted or downsized to the planned dimensions without cropping or hidden upscaling.`);
        if (deliverable.kind === "video")
            lines.push("Experimental video adapter: AIsa's documented Wan gateway payload conflicts with other published contracts and has not been live-verified in this release. This deliverable explicitly opts in to a potentially failing paid request; approval must cover that uncertainty. A matching public HTTPS reference photo is required; automatic upload is unavailable.");
        if (deliverable.constraints)
            lines.push(`Media acceptance constraints: ${Object.entries(deliverable.constraints).map(([key, value]) => `${key}: ${value}`).join("; ")}.`);
        lines.push(`Estimated base cost: USD ${deliverable.estimatedCostUsd.toFixed(4)}.`, "", deliverable.prompt, "", "Acceptance checks:", "", ...deliverable.successCriteria.map(item => `- ${item}`), "");
        if (deliverable.pricingSource)
            lines.push(`Pricing evidence: ${deliverable.pricingSource}; checked ${deliverable.pricingCheckedAt}.`, "");
    }
    const maxAttemptEstimate = playbook.budget.estimatedTotalUsd * playbook.budget.maxAttemptsPerDeliverable;
    lines.push("## Budget and execution limits", "", `Base estimate: USD ${playbook.budget.estimatedTotalUsd.toFixed(4)}. Maximum ${playbook.budget.maxAttemptsPerDeliverable} submitted attempts per deliverable. If every attempt costs the estimate, the attempt allowance totals USD ${maxAttemptEstimate.toFixed(4)}. The brief's estimate limit is USD ${state.brief.budget.maxEstimatedCostUsd.toFixed(4)}.`, "", "These are estimates, not an enforced provider billing cap. Prices, failed requests, research charges, and retries may change actual spending. Ambiguous submissions must be reconciled before retrying.", "", ...playbook.approvalNotes.map(note => `- ${note}`), "", "## Approval", "", `Exact approval hash: \`${approvalHash(state)}\``, "", "Review this version and confirm it or describe the changes you want. Generation remains blocked until the user's explicit approval is recorded. Changes to product references, facts, research, or this plan invalidate approval.", "");
    return lines.join("\n");
}
