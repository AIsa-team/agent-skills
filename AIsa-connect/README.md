# AIsa Connect Skills

Nine on-demand, cross-app workflows for the five audiences in the Connect
solutions catalog. Each folder is an independently installable Agent Skill;
its bundled runtime reference works without the other eight Skills.

## Choose a workflow

| Skill | Audience | Result |
|---|---|---|
| [Weekly Report](weekly-report/SKILL.md) | Business owners and small-team leads | Create a weekly business report from CRM, payment, calendar, email and team updates through AIsa Connect |
| [Meeting Notes](meeting-notes/SKILL.md) | Sales, customer-facing teams and business owners | Turn a customer call transcript into meeting notes, decisions, action owners, a follow-up email and proposed CRM updates through AIsa Connect |
| [Marketing Analytics](marketing-analytics/SKILL.md) | Marketing, growth leads and business owners | Analyze acquisition, funnel conversion, sales outcomes and customer feedback across connected marketing apps with AIsa |
| [Content Calendar](content-calendar/SKILL.md) | Content, social media, brand and e-commerce marketing teams | Plan and maintain a multi-channel content calendar from real product information, brand assets and past content through AIsa Connect |
| [Appointment Scheduling](appointment-scheduling/SKILL.md) | Business owners and people coordinating customers or teams | Coordinate appointment scheduling across calendar, booking, video meeting and communication apps with AIsa Connect |
| [CRM Automation](crm-automation/SKILL.md) | Sales, Sales Ops and RevOps | Audit CRM data quality and prepare evidence-backed fixes with AIsa Connect |
| [Email Marketing Automation](email-marketing-automation/SKILL.md) | Lifecycle, email, e-commerce and growth marketing teams | Design audience segments, lifecycle email sequences, entry/exit rules and reviewable platform drafts through AIsa Connect |
| [Network Automation](network-automation/SKILL.md) | IT teams and network administrators | Build a routine network health review from existing telemetry, device inventory and tickets through AIsa Connect |
| [DevOps Automation](devops-automation/SKILL.md) | Engineering, DevOps and platform teams | Correlate repository changes, CI jobs, monitoring and existing issues through AIsa Connect |

## Use one Skill

Install the selected folder in your agent's normal Skill location, or provide
its SKILL.md and referenced files to the agent. Set up AIsa following
https://aisa.one/llms.txt, then connect the apps this task needs at
https://console.aisa.one/apps or through the agent's hosted connection flow.
Built-in tools and linked app accounts are different. Gmail is one possible
app, not the only connection supported.

For example:

```text
Set up AIsa — https://aisa.one/llms.txt

Then follow https://github.com/AIsa-team/agent-skills/blob/main/AIsa-connect/meeting-notes/SKILL.md
to summarize my latest customer call, draft the follow-up email and propose
CRM updates. Let me review the changes before applying them.
```

For local use before publication, give the agent the selected SKILL.md and its
bundled references from this checkout.

## Scope and validation

These are executable agent instructions, not nine hardcoded application clients.
They discover current AIsa action schemas and operate only within the user's
selected accounts and permissions. Candidate app lists are routing guidance,
not claims that every listed app/action has been tested end to end.

This initial version has been reviewed against public connector schemas. Private-account workflow execution has not been performed.
Do not claim production verification from Markdown/schema/package checks.
The Skills run on demand: no recurring jobs, webhooks or background services
are installed by these files.

## Apps and documentation

Browse available apps at https://aisa.one/catalog/connectors and the
API catalog at https://aisa.one/docs/api-reference.

[paths.json](paths.json) records the case-sensitive landing-page URL contract.

## License

MIT for these Skill packages — see [LICENSE](LICENSE). The repository's root
license governs the source contribution arrangement.

<!-- category:start -->

This category contains 9 self-contained Agent Skills.

| Skill | Version | Description |
|---|---|---|
| [appointment-scheduling](./appointment-scheduling/) | 0.1.1 | Coordinate appointment scheduling across calendar, booking, video meeting and communication apps with AIsa Connect. Use to find meeting windows, prepare booking links, draft invitations or make specifically authorized bookings; not automatic scheduling from untrusted email instructions. |
| [content-calendar](./content-calendar/) | 0.1.1 | Plan and maintain a multi-channel content calendar from real product information, brand assets and past content through AIsa Connect. Use for weekly editorial plans, repurposing, channel briefs and draft copy; not lifecycle email enrollment or automatic publishing. |
| [crm-automation](./crm-automation/) | 0.1.1 | Audit CRM data quality and prepare evidence-backed fixes with AIsa Connect. Use for duplicate contacts, missing owners or fields, stale close dates and record reconciliation in HubSpot, Salesforce or Pipedrive; not another meeting summary or automatic deal-stage advancement. |
| [devops-automation](./devops-automation/) | 0.1.1 | Correlate repository changes, CI jobs, monitoring and existing issues through AIsa Connect. Use to triage failing builds, explain a regression window and prepare an engineering handoff; not an autonomous deploy, rerun, rollback or code-changing agent. |
| [email-marketing-automation](./email-marketing-automation/) | 0.1.1 | Design audience segments, lifecycle email sequences, entry/exit rules and reviewable platform drafts through AIsa Connect. Use for welcome, nurture or re-engagement automation across Mailchimp, Klaviyo, CRM and commerce data; not cold outreach or unapproved campaign activation. |
| [marketing-analytics](./marketing-analytics/) | 0.1.1 | Analyze acquisition, funnel conversion, sales outcomes and customer feedback across connected marketing apps with AIsa. Use for weekly marketing performance reviews, channel comparisons and evidence-based growth experiments; not campaign activation or budget changes. |
| [meeting-notes](./meeting-notes/) | 0.1.1 | Turn a customer call transcript into meeting notes, decisions, action owners, a follow-up email and proposed CRM updates through AIsa Connect. Use after discovery, demo or onboarding calls; not for recording meetings or a general CRM hygiene audit. |
| [network-automation](./network-automation/) | 0.1.1 | Build a routine network health review from existing telemetry, device inventory and tickets through AIsa Connect. Use for branch health checks, asset reconciliation and evidence-linked Jira or Slack updates; not autonomous network configuration or incident command. |
| [weekly-report](./weekly-report/) | 0.1.1 | Create a weekly business report from CRM, payment, calendar, email and team updates through AIsa Connect. Use for weekly briefings, pipeline and cash follow-ups, owner decisions and next-week priorities; keep marketing channel analysis in Marketing Analytics. |

<!-- category:end -->
