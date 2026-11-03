#!/usr/bin/env node
import { readFile } from "node:fs/promises";
import { assessmentSummary, inspectBrief, parseAssessment, parseBrief, ValidationError } from "./model.js";
import { renderAssessment } from "./report.js";
const usage = "Usage: node dist/cli.js <inspect-brief|validate|render> <input.json>\nLocal validation/reporting only; no network calls, authentication or legal clearance.\nResults go to stdout. Invalid input exits 1; usage errors exit 2.";
const [command, file, ...extra] = process.argv.slice(2);
if (command === "--help" && !file) {
    console.log(usage);
}
else if (!["inspect-brief", "validate", "render"].includes(command ?? "") || !file || extra.length) {
    console.error(usage);
    process.exitCode = 2;
}
else {
    try {
        const input = JSON.parse(await readFile(file, "utf8"));
        if (command === "inspect-brief")
            console.log(JSON.stringify(inspectBrief(parseBrief(input)), null, 2));
        else {
            const assessment = parseAssessment(input);
            if (command === "validate")
                console.log(JSON.stringify(assessmentSummary(assessment), null, 2));
            else
                process.stdout.write(renderAssessment(assessment));
        }
    }
    catch (error) {
        const errors = error instanceof ValidationError ? error.problems : [error instanceof Error ? error.message : String(error)];
        console.error(JSON.stringify({ valid: false, errors }, null, 2));
        process.exitCode = 1;
    }
}
