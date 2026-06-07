"""Generated library courses rendered through the reusable course template."""

GRAYSCALE_INTERVIEW_PREP = {
    "meta": {
        "title": "Grayscale Interview Prep",
        "subtitle": "Principal PM interview practice",
        "learner": "adult",
        "learningStyle": "practice",
    },
    "modules": [
        {
            "type": "overview",
            "id": "overview",
            "label": "1. Brief",
            "data": {
                "kicker": "Interview prep",
                "headline": "Turn the Grayscale story into product operating judgment.",
                "body": (
                    "This course helps you practice the Principal PM narrative: why the role exists, "
                    "how digital asset operations create product risk, and how to answer with a "
                    "measured operating model instead of a generic platform pitch."
                ),
                "cards": [
                    {"tag": "Company", "title": "Asset manager context",
                     "text": "Frame Grayscale as a regulated digital asset manager where product, finance, operations, compliance, and vendors must agree on trusted facts."},
                    {"tag": "Role", "title": "Principal PM signal",
                     "text": "Show ownership across ambiguity: define the control boundary, prioritize by risk, and align executives around measurable operating outcomes."},
                    {"tag": "Risk", "title": "Evidence beats optimism",
                     "text": "Every answer should make auditability, source freshness, exception routing, and vendor dependency visible."},
                ],
                "stepsTitle": "Practice path",
                "steps": [
                    "Name the operating-model problem under the workflow problem.",
                    "Separate raw evidence, authoritative state, and human workflow.",
                    "Answer security and vendor-risk pushback with concrete controls.",
                    "Close with measurable first-90-day outcomes.",
                ],
            },
        },
        {
            "type": "concept_cards",
            "id": "concepts",
            "label": "2. Concepts",
            "data": {
                "intro": "Use these frames to keep answers specific to Grayscale.",
                "cards": [
                    {
                        "badge": "Frame",
                        "name": "Operating Model",
                        "fields": [
                            {"label": "Definition", "text": "A repeatable way to detect exceptions, assign owners, preserve evidence, and prove what happened.", "tone": "info"},
                            {"label": "Interview use", "text": "Say the visible problem is manual workflow, but the deeper issue is lack of shared ground truth.", "tone": "good"},
                        ],
                        "highlight": {"label": "Trap", "q": "What is the common mistake?", "a": "Jumping straight to tooling before naming ownership, controls, and evidence."},
                    },
                    {
                        "badge": "Architecture",
                        "name": "Control Boundary",
                        "fields": [
                            {"label": "Definition", "text": "The line between systems that own truth and systems that display, route, or approve work.", "tone": "info"},
                            {"label": "Interview use", "text": "RDS/S3 own authoritative records and replayable evidence; no-code owns authenticated workflow and approvals.", "tone": "good"},
                        ],
                        "highlight": {"label": "Trap", "q": "What should no-code not become?", "a": "A shadow database or hidden rules engine."},
                    },
                    {
                        "badge": "Risk",
                        "name": "Vendor Dependency",
                        "fields": [
                            {"label": "Definition", "text": "Custodians, fund admins, indexers, validators, cloud, no-code, and AI providers can all become operational dependencies.", "tone": "warn"},
                            {"label": "Interview use", "text": "Discuss SLAs, incident notice, format-change processes, evidence rights, BCP/DR posture, and exit paths.", "tone": "good"},
                        ],
                        "highlight": {"label": "Trap", "q": "What sounds weak?", "a": "Saying vendors are monitored without explaining ownership and escalation."},
                    },
                ],
            },
        },
        {
            "type": "drag_sort",
            "id": "sort",
            "label": "3. Sort",
            "data": {
                "title": "Put each responsibility in the right layer",
                "intro": "This drill tests whether your architecture story has a clean control boundary.",
                "buckets": [
                    {"id": "truth", "label": "Authoritative truth", "hint": "State, mappings, replay, evidence"},
                    {"id": "workflow", "label": "Human workflow", "hint": "Review, approval, queues, display"},
                    {"id": "risk", "label": "Risk governance", "hint": "Controls, access, vendor posture"},
                ],
                "items": [
                    {"id": "raw", "label": "Immutable raw payloads in object storage", "detail": "Replayable source evidence", "bucket": "truth"},
                    {"id": "approval", "label": "Exception approval queue", "detail": "Human workflow state", "bucket": "workflow"},
                    {"id": "audit", "label": "Audit-log export validation", "detail": "Security and compliance control", "bucket": "risk"},
                    {"id": "mapping", "label": "Fund/account mapping table", "detail": "Authoritative business mapping", "bucket": "truth"},
                    {"id": "sso", "label": "SSO, MFA, RBAC, access review", "detail": "Identity control", "bucket": "risk"},
                    {"id": "dashboard", "label": "Ops dashboard showing stale data warnings", "detail": "Workflow display", "bucket": "workflow"},
                ],
            },
        },
        {
            "type": "flashcards",
            "id": "cards",
            "label": "4. Recall",
            "data": {
                "cards": [
                    {"q": "What is the strongest one-line Grayscale operating-model frame?", "a": "The visible issue is manual work; the real issue is lack of shared ground truth and operating evidence."},
                    {"q": "What should AWS own in the no-code/AWS split?", "a": "Raw evidence, authoritative state, replay, access boundaries, monitoring, and durable orchestration where needed."},
                    {"q": "What should no-code own?", "a": "Authenticated human workflow, display, approvals, queues, and audit export, not authoritative state."},
                    {"q": "Name four vendor-risk questions.", "a": "SLA, incident notice, format-change process, evidence rights, BCP/DR posture, exit plan."},
                    {"q": "Why do timestamps matter?", "a": "Source, observed, ingestion, and data-as-of timestamps prevent stale or partial data from being treated as current."},
                    {"q": "How do you avoid one-off chain workflows?", "a": "Preserve chain-specific raw data, normalize through adapters, and emit a canonical event envelope."},
                    {"q": "What makes the first 90 days credible?", "a": "Risk-ranked workflow selection, live evidence, observable controls, and measurable exception reduction."},
                    {"q": "What is the no-code security trap?", "a": "Letting it become a shadow database, uncontrolled admin layer, or hidden rules engine."},
                ],
            },
        },
        {
            "type": "challenge",
            "id": "quiz",
            "label": "5. Quiz",
            "data": {
                "kind": "quiz",
                "title": "Interview pushback",
                "intro": "Pick the answer that sounds most like a Principal PM.",
                "startLabel": "Start quiz",
                "rounds": [
                    {
                        "question": "An executive asks why this is not just an automation project. What is the best answer?",
                        "opts": [
                            "Automation is faster, so we can do more with fewer people.",
                            "Automation matters, but the core product problem is trusted operating evidence across systems and teams.",
                            "The main issue is picking the right no-code vendor.",
                            "Engineering can solve it after requirements are complete.",
                        ],
                        "correct": 1,
                        "exp": "A Principal PM names the underlying operating model, not just the surface workflow.",
                    },
                    {
                        "question": "Security asks whether no-code is a risk. What answer is strongest?",
                        "opts": [
                            "No-code is safe if the vendor is reputable.",
                            "No-code is risky only for external users.",
                            "It is acceptable when limited to authenticated workflow, display, and approvals, while truth and evidence stay in controlled systems.",
                            "We can avoid risk by not exporting audit logs.",
                        ],
                        "correct": 2,
                        "exp": "The answer names boundaries and controls instead of hand-waving vendor trust.",
                    },
                    {
                        "question": "A custodian feed is late on a NAV-sensitive workflow. What should happen first?",
                        "opts": [
                            "Freeze or label downstream outputs as data-as-of, preserve evidence, and route by impact.",
                            "Ignore it if the last run succeeded.",
                            "Ask the no-code admin to override the record.",
                            "Retrain an AI model on historical vendor issues.",
                        ],
                        "correct": 0,
                        "exp": "Integrity incidents need containment, evidence, impact routing, and escalation.",
                    },
                ],
            },
        },
        {
            "type": "teach_back",
            "id": "teach",
            "label": "6. Teach",
            "data": {
                "title": "Say it out loud",
                "intro": "Practice crisp interview answers.",
                "prompts": [
                    {
                        "q": "Explain the no-code/AWS split in 45 seconds.",
                        "keyPoints": ["AWS owns truth and evidence", "No-code owns workflow/display/approval", "Audit and admin controls are explicit"],
                        "sample": "I would make the control boundary explicit: AWS preserves raw evidence in S3, owns authoritative state in RDS, and monitors freshness and failures. No-code presents workflow state, routes approvals, and exports audit logs. It should never become the database or rules engine.",
                    },
                    {
                        "q": "Explain how you would handle chain-specific complexity.",
                        "keyPoints": ["Raw chain-specific payloads", "Explicit adapters", "Canonical event envelope"],
                        "sample": "I would not force every chain into the same ingress shape. I would preserve chain-specific raw payloads, normalize through adapter Lambdas, and emit a canonical event envelope for downstream reconciliation and workflow.",
                    },
                ],
            },
        },
        {
            "type": "glossary",
            "id": "glossary",
            "label": "7. Terms",
            "data": {
                "intro": "Terms to use precisely in interview answers.",
                "terms": [
                    {"t": "Control boundary", "d": "The explicit split between systems that own truth and systems that route or display workflow."},
                    {"t": "Canonical event envelope", "d": "A normalized downstream record that carries chain/source metadata plus common operational fields."},
                    {"t": "Data-as-of", "d": "A visible freshness signal showing when the data was sourced, observed, and ingested."},
                    {"t": "Shadow database", "d": "A workflow tool or spreadsheet becoming an unofficial source of truth."},
                    {"t": "Segregation of duties", "d": "Separating submitter, reviewer, approver, mapper, and admin responsibilities."},
                ],
            },
        },
        {
            "type": "cheatsheet",
            "id": "cheatsheet",
            "label": "8. Sheet",
            "data": {
                "title": "Interview cheat sheet",
                "intro": "Keep these answer anchors ready.",
                "blocks": [
                    {"title": "Opening thesis", "text": "The product opportunity is to create trusted operating evidence for a growing digital asset fund suite."},
                    {"title": "Security answer", "items": ["SSO/MFA/RBAC", "Audit-log export", "Environment separation", "Admin override logging", "Periodic access review"]},
                    {"title": "Vendor answer", "items": ["Owner", "SLA", "Format-change notice", "Incident notice", "Evidence rights", "Exit plan"]},
                    {"title": "90-day proof", "items": ["One high-risk workflow live", "Exception SLA visible", "Replayable evidence", "Controls instrumented", "Reusable operating pattern"]},
                ],
            },
        },
    ],
}


GRAYSCALE_PPM_MASTERY = {
    "meta": {
        "title": "Grayscale PPM Mastery",
        "subtitle": "Product, fintech, Web3, architecture",
        "learner": "adult",
        "learningStyle": "mixed",
    },
    "modules": [
        {
            "type": "overview",
            "id": "overview",
            "label": "1. Map",
            "data": {
                "kicker": "Mastery course",
                "headline": "Connect product strategy, digital assets, and operating architecture.",
                "body": "This course turns the Grayscale prep material into a reusable product leadership study path.",
                "cards": [
                    {"tag": "Market", "title": "Digital asset products", "text": "Spot products, staking mechanics, fund operations, and client trust all shape product decisions."},
                    {"tag": "System", "title": "Operating platform", "text": "Ingress, normalization, authoritative state, workflow, monitoring, and audit evidence are the core layers."},
                    {"tag": "Leadership", "title": "PPM behavior", "text": "Senior PM impact comes from prioritization, alignment, mentoring, execution discipline, and risk judgment."},
                ],
                "stepsTitle": "Mastery path",
                "steps": ["Learn the product thesis", "Map the operating system", "Practice risk decisions", "Rehearse leadership answers"],
            },
        },
        {
            "type": "visual_map",
            "id": "system-map",
            "label": "2. System",
            "data": {
                "title": "Digital asset operating map",
                "intro": "Follow the path from external source data to executive confidence.",
                "nodes": [
                    {"id": "sources", "label": "Sources", "tag": "Feeds", "summary": "Custodian, fund admin, indexer, validator, and chain data."},
                    {"id": "ingress", "label": "Ingress", "tag": "API/SQS", "summary": "Authenticated payloads, schema validation, idempotency, backpressure."},
                    {"id": "normalize", "label": "Normalize", "tag": "Adapters", "summary": "Chain-specific parsing into canonical event records."},
                    {"id": "truth", "label": "Truth", "tag": "RDS/S3", "summary": "Authoritative state plus immutable evidence."},
                    {"id": "workflow", "label": "Workflow", "tag": "No-code", "summary": "Queues, approvals, display, and audit export."},
                    {"id": "controls", "label": "Controls", "tag": "Risk", "summary": "Freshness, access, anomaly checks, escalation, reporting impact."},
                ],
                "links": [
                    {"from": "sources", "to": "ingress", "label": "send"},
                    {"from": "ingress", "to": "normalize", "label": "validate"},
                    {"from": "normalize", "to": "truth", "label": "store"},
                    {"from": "truth", "to": "workflow", "label": "present"},
                    {"from": "workflow", "to": "controls", "label": "evidence"},
                ],
            },
        },
        {
            "type": "concept_cards",
            "id": "concepts",
            "label": "3. Concepts",
            "data": {
                "intro": "These concepts show up across strategy, architecture, and leadership questions.",
                "cards": [
                    {
                        "badge": "Product",
                        "name": "Fund-suite scalability",
                        "fields": [
                            {"label": "Idea", "text": "Product expansion increases protocol-specific exceptions and operational evidence needs.", "tone": "info"},
                            {"label": "Action", "text": "Prioritize workflows by regulatory, NAV, client, and exception-volume impact.", "tone": "good"},
                        ],
                        "highlight": {"label": "Trap", "q": "What is too shallow?", "a": "Saying scale means more dashboards instead of more reliable operating evidence."},
                    },
                    {
                        "badge": "Technical",
                        "name": "Canonical model",
                        "fields": [
                            {"label": "Idea", "text": "Downstream systems need stable event concepts without erasing chain-specific mechanics.", "tone": "info"},
                            {"label": "Action", "text": "Keep raw payloads immutable and map into canonical records with extension fields.", "tone": "good"},
                        ],
                        "highlight": {"label": "Trap", "q": "What breaks?", "a": "Flattening Bitcoin, EVM, Solana, and oracle events into fake sameness at ingress."},
                    },
                    {
                        "badge": "Leadership",
                        "name": "Senior alignment",
                        "fields": [
                            {"label": "Idea", "text": "Executives need a small number of risk-ranked bets with clear proof points.", "tone": "info"},
                            {"label": "Action", "text": "Translate technical architecture into operating risk, client trust, and audit readiness.", "tone": "good"},
                        ],
                        "highlight": {"label": "Trap", "q": "What sounds junior?", "a": "Listing features without explaining the executive decision they support."},
                    },
                ],
            },
        },
        {
            "type": "sequence",
            "id": "sequence",
            "label": "4. Sequence",
            "data": {
                "title": "Order the operating rollout",
                "intro": "A credible rollout creates proof before broad platform claims.",
                "modes": [
                    {
                        "key": "rollout",
                        "label": "First 90 days",
                        "items": [
                            {"id": "risk", "label": "Rank workflows by risk and exception volume", "why": "Start where control value is highest."},
                            {"id": "source", "label": "Define sources, owners, and freshness requirements", "why": "Evidence needs ownership."},
                            {"id": "slice", "label": "Ship one high-risk workflow with controls", "why": "Prove the pattern."},
                            {"id": "measure", "label": "Measure SLA, exceptions, stale data, and audit completeness", "why": "Make value visible."},
                            {"id": "expand", "label": "Expand to adjacent workflows", "why": "Scale the operating model."},
                        ],
                        "correct": ["risk", "source", "slice", "measure", "expand"],
                    },
                ],
            },
        },
        {
            "type": "flashcards",
            "id": "cards",
            "label": "5. Recall",
            "data": {
                "cards": [
                    {"q": "What is the product value of the operating platform?", "a": "It gives teams trusted state, exception visibility, and audit-ready evidence as the fund suite scales."},
                    {"q": "What fields belong in a canonical event envelope?", "a": "Chain, network, source, payload URI, event id, event type, asset, amount, account refs, block/slot height, timestamps, finality status."},
                    {"q": "How should AI appear in the architecture?", "a": "Assistive until deterministic state is trusted; never the sole owner of NAV-sensitive truth."},
                    {"q": "What makes chain data hard?", "a": "Different execution, state, finality, account, and event models across protocols."},
                    {"q": "Name three executive proof points.", "a": "Lower exception cycle time, fewer stale downstream outputs, stronger audit completeness."},
                    {"q": "What is the mentoring angle?", "a": "Teach PMs to define control boundaries, measurable outcomes, and risk-ranked scopes."},
                    {"q": "What makes a vendor incident an integrity incident?", "a": "Untrusted source data can corrupt downstream state, reporting, client outputs, or NAV-sensitive workflows."},
                    {"q": "What is the strongest prioritization principle?", "a": "Regulatory, NAV, client, and operational risk before convenience."},
                ],
            },
        },
        {
            "type": "challenge",
            "id": "rounds",
            "label": "6. Scenarios",
            "data": {
                "kind": "rounds",
                "title": "PPM scenario rounds",
                "intro": "Choose the strongest product move.",
                "startLabel": "Start rounds",
                "rounds": [
                    {
                        "title": "Protocol expansion",
                        "scenario": "A new asset has different finality and event semantics from existing assets.",
                        "question": "What should the platform team do?",
                        "opts": [
                            {"label": "Copy the existing parser", "detail": "Fast but hides semantic differences."},
                            {"label": "Build an explicit adapter", "detail": "Preserve raw specifics, emit canonical events downstream."},
                            {"label": "Wait for the fund admin", "detail": "Outsources the product model."},
                        ],
                        "correct": 1,
                        "exp": "Explicit adapters prevent chain complexity from leaking everywhere while preserving source truth.",
                    },
                    {
                        "title": "Executive tradeoff",
                        "scenario": "Ops wants faster workflow, Security wants tighter control, Finance wants reliable reporting.",
                        "question": "What is the best PM framing?",
                        "opts": [
                            {"label": "Pick the loudest stakeholder", "detail": "Creates local optimization."},
                            {"label": "Frame by operating risk and evidence", "detail": "Align speed, control, and reporting around shared proof."},
                            {"label": "Defer until all requirements are done", "detail": "Avoids senior judgment."},
                        ],
                        "correct": 1,
                        "exp": "Senior PMs convert cross-functional tension into a decision framework.",
                    },
                ],
            },
        },
        {
            "type": "challenge",
            "id": "timed",
            "label": "7. Speed",
            "data": {
                "kind": "timed",
                "title": "Fast signal check",
                "intro": "Answer quickly to test whether the frames are internalized.",
                "startLabel": "Start speed round",
                "timer": 20,
                "rounds": [
                    {"question": "Which layer owns authoritative state?", "opts": ["No-code UI", "RDS/S3 controlled backend", "Chat assistant", "Slide deck"], "correct": 1, "exp": "Truth and replayable evidence stay in controlled backend systems."},
                    {"question": "What should be visible when data is stale?", "opts": ["Data-as-of status", "Only a hidden log", "A manual note", "Nothing until fixed"], "correct": 0, "exp": "Freshness must be visible to prevent bad downstream decisions."},
                    {"question": "What is the best expansion pattern?", "opts": ["One bespoke workflow per asset", "Reusable adapters plus canonical events", "Manual spreadsheet review", "All logic in no-code"], "correct": 1, "exp": "Reusable patterns scale without pretending every protocol is identical."},
                ],
            },
        },
        {
            "type": "glossary",
            "id": "glossary",
            "label": "8. Terms",
            "data": {
                "intro": "Use these terms fluently.",
                "terms": [
                    {"t": "Finality", "d": "Confidence that a transaction or state transition will not be reversed."},
                    {"t": "Idempotency", "d": "Processing repeated payloads without creating duplicate business effects."},
                    {"t": "Backpressure", "d": "A system's way of absorbing or slowing inbound work when downstream components lag."},
                    {"t": "Canonical record", "d": "A normalized representation downstream consumers can trust."},
                    {"t": "BCP/DR", "d": "Business continuity and disaster recovery expectations for critical vendors and systems."},
                ],
            },
        },
        {
            "type": "cheatsheet",
            "id": "sheet",
            "label": "9. Sheet",
            "data": {
                "title": "PPM mastery sheet",
                "intro": "Use this to rehearse before interviews or product reviews.",
                "blocks": [
                    {"title": "Product thesis", "text": "Build trusted operating evidence so digital asset product expansion does not outpace controls."},
                    {"title": "Architecture line", "text": "Raw source payloads stay immutable; adapters normalize; controlled storage owns truth; workflow tools route human decisions."},
                    {"title": "Risk lens", "items": ["NAV impact", "Regulatory impact", "Client output impact", "Exception volume", "Vendor dependency"]},
                    {"title": "Leadership lens", "items": ["Name the decision", "Align by risk", "Define proof points", "Mentor repeatable thinking", "Ship a measurable slice"]},
                ],
            },
        },
    ],
}


GENERATED_COURSES = {
    "grayscale-interview-prep-generated.html": {
        "id": "grayscale-interview-prep",
        "course": GRAYSCALE_INTERVIEW_PREP,
    },
    "grayscale-ppm-mastery-generated.html": {
        "id": "grayscale-ppm-mastery",
        "course": GRAYSCALE_PPM_MASTERY,
    },
}
