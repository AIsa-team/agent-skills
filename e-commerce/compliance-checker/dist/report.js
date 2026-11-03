import { assessmentSummary } from "./model.js";
// Supplied text remains data: avoid embedding HTML, Markdown links or headings from source excerpts.
function plain(value) {
    return value.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")
        .replace(/[\\`*_{}\[\]()#+.!|~-]/gu, "\\$&").replace(/\r?\n/gu, " ");
}
function missingLabel(field, brief) {
    if (field === "product.name")
        return "Product to be sold";
    if (field === "destinations")
        return "Destination country or region";
    if (field === "plannedSale.start")
        return "Planned selling start";
    const match = /^destinations\[(\d+)\]\.(country|platforms)$/u.exec(field);
    if (match?.[2] === "country")
        return "Specific EU destination countries; national requirements remain unassessed";
    if (match?.[2] === "platforms")
        return `Sales platform for ${brief.destinations?.[Number(match[1])]?.country ?? "the destination"}`;
    return "Additional selling-plan information";
}
export function renderAssessment(a) {
    const result = assessmentSummary(a);
    const b = a.brief;
    const output = [
        "# Compliance assessment",
        "",
        ...(a.synthetic ? ["**SYNTHETIC EXAMPLE — no live research or legal conclusions.**", ""] : []),
        `Assessment date: ${b.asOf}`,
        "",
        `State: **${result.preliminary ? "Preliminary" : "Scoped review"}**. Coverage: **${result.coverage}**.`,
        "",
        "This report covers only the supplied scope and evidence. It does not provide overall legal clearance, a binding classification, or verification of document authenticity. Unlisted requirements remain unassessed.",
        "",
        `Scope: ${plain(a.scope)}`,
        "",
        "## Selling plan",
        "",
        `- Product: ${plain(b.product?.name ?? "Unknown")}`,
        `- Planned sales: ${b.plannedSale?.start ?? "Start unknown"} → ${b.plannedSale?.end ?? "End unknown"}${b.plannedSale?.note ? ` (${plain(b.plannedSale.note)})` : ""}`,
        ...((b.destinations?.length ? b.destinations : [undefined]).map(d => `- Destination: ${d ? `${d.country}${d.subdivision ? ` / ${plain(d.subdivision)}` : ""}; platforms: ${d.platforms?.length ? d.platforms.map(p => `${plain(p.name)}${p.site ? ` (${plain(p.site)})` : ""}`).join(", ") : "unknown"}` : "unknown"}`)),
        `- Seller location: ${plain(b.seller?.location ?? "Unknown")}; ship from: ${plain(b.seller?.shipFrom ?? "Unknown")}; fulfilment: ${plain(b.seller?.fulfilment ?? "Unknown")}`,
        ...(b.product?.facts ?? []).map(f => `- Product fact supplied: ${plain(f)}`),
        "",
        "## Open information and coverage",
        "",
        ...(result.missingCoreFields.length ? result.missingCoreFields.map(f => `- Still needed: ${plain(missingLabel(f, b))}`) : ["- Core intake fields recorded; additional product-specific facts may still be needed."]),
        ...(b.unknowns ?? []).map(v => `- Unresolved: ${plain(v)}`),
        ...result.warnings.map(v => `- ${plain(v)}`),
        "",
        "## Findings and next actions",
        "",
    ];
    if (!a.findings.length)
        output.push("No findings supplied. Requirements have not been assessed.", "");
    for (const f of a.findings) {
        output.push(`### ${plain(f.id)}: ${plain(f.title)}`, "", `- Status: **${f.status}**${f.status === "no-issue-found" ? " — limited to this finding's stated scope and supplied evidence; not clearance" : ""}`, `- Kind: ${f.kind}; jurisdiction: ${f.jurisdiction}`, `- Scope: ${plain(f.scope)}`, `- Applicability: ${plain(f.applicability.reason)}`, `- Timing: ${f.applicability.temporalStatus}; effective ${f.applicability.effectiveFrom ?? "start not established"} → ${f.applicability.effectiveTo ?? "end not established"}; rule status: ${f.applicability.ruleStatus ?? "not recorded"}`, `- Finding: ${plain(f.explanation)}`, `- Action: ${plain(f.action)}`, `- Source IDs: ${f.sourceIds.length ? f.sourceIds.map(plain).join(", ") : "None — no source-backed conclusion"}`, "");
    }
    output.push("## Evidence register", "");
    if (!a.evidence.length)
        output.push("No source evidence supplied.", "");
    for (const e of a.evidence) {
        output.push(`### ${plain(e.id)}: ${plain(e.title)}`, "", `- URL: <${new URL(e.url).href.replaceAll("<", "%3C").replaceAll(">", "%3E")}>`, `- Authority: ${e.authority}; jurisdictions: ${e.jurisdictions.join(", ")}`, `- Accessed: ${e.accessedAt}; inspected: ${e.inspected ? "yes (declared by the researcher)" : "no — not verified evidence"}`, `- Supplied excerpt: ${plain(e.excerpt)}`, "");
    }
    return output.join("\n");
}
