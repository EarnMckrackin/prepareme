/* ============================================================
   GRAYSCALE-LAB-DATA.JSX — Interview + mastery lab courses
   ============================================================ */

const GRAYSCALE_INTERVIEW_PREP_LAB = {
  id: 'grayscale-interview-prep',
  title: 'Grayscale Interview Prep',
  series: 'Principal PM Interview Lab',
  level: 3,
  moduleLabel: 'A',
  description: 'High-pressure answer practice for the Grayscale Principal PM loop: executive narrative, AI point of view, architecture defense, risk, and live pushback.',
  tags: ['interview', 'grayscale', 'principal-pm', 'ai', 'risk'],
  stages: [
    {
      id: 'gi-s1-story',
      title: 'Executive Story',
      subtitle: 'The one-line thesis',
      icon: '◆',
      why: 'The room needs to hear that you understand the operating problem underneath the workflow. Your edge is not a feature list; it is the ability to turn manual work into a controlled operating model.',
      concepts: [
        {
          id: 'gi-thesis',
          title: 'The Core Thesis',
          why: {
            scenario: 'Diana or Max asks: "What is the real problem here?" If you answer with dashboards, queues, or no-code, you sound tactical.',
            tension: 'Lead with the operating-model problem before the solution architecture.'
          },
          what: {
            definition: 'Best one-liner',
            body: '**The visible issue is manual work; the real issue is lack of shared ground truth and operating evidence.** The product answer is a controlled workflow that makes source freshness, exceptions, ownership, and audit evidence visible.'
          },
          what2: {
            definition: 'How to say it live',
            body: 'Start with risk and trust, then architecture: "I would use one high-risk workflow to prove the pattern: authoritative records, immutable source evidence, human review, and measurable controls. Then expand by exception volume and regulatory impact."'
          },
          example: {
            label: 'Weak vs strong framing',
            comparison: {
              bad: { label: 'Too tactical', content: 'I built a workflow to automate reconciliation and make Ops faster.' },
              good: { label: 'Principal PM signal', content: 'I designed a repeatable operating model: source evidence, authoritative state, exception routing, ownership, and auditability.' }
            }
          },
          drill: {
            type: 'choice',
            question: 'Which opening best signals Principal PM judgment?',
            options: [
              'I would start by picking a no-code tool so the team can move quickly.',
              'The visible issue is manual work; the deeper issue is lack of shared truth and operating evidence.',
              'I would ask Engineering to build the whole platform before launch.',
              'The main benefit is fewer spreadsheet updates for Ops.'
            ],
            correct: 1,
            explanation: 'The strongest answer names the operating risk before naming tools. It gives executives a reason to care beyond productivity.'
          }
        },
        {
          id: 'gi-company',
          title: 'Grayscale Context',
          why: {
            scenario: 'An interviewer tests whether you understand why this is different from generic SaaS workflow work.',
            tension: 'Digital asset operations sit between product growth, regulatory posture, finance accuracy, vendor data, custody, and client trust.'
          },
          what: {
            definition: 'Context to carry',
            body: 'Grayscale is a regulated digital asset manager. Product expansion increases protocol-specific exceptions, vendor dependencies, custody questions, and reporting sensitivity. A PM here must connect customer/product outcomes to operating controls.'
          },
          example: {
            label: 'What to tie together',
            table: [
              { scenario: 'New asset exposure', fix: 'Product growth', reason: 'More fund coverage increases operational variants.' },
              { scenario: 'Custodian or fund-admin feed', fix: 'Vendor dependency', reason: 'Freshness, format changes, and incident notice become product risks.' },
              { scenario: 'NAV-sensitive workflow', fix: 'Control posture', reason: 'Evidence and escalation matter as much as speed.' }
            ]
          },
          drill: {
            type: 'scenario',
            question: 'You get asked: "Why does this role matter now?" Which answer is strongest?',
            options: [
              { label: 'Because Ops wants fewer manual steps.', detail: 'True, but too narrow.' },
              { label: 'Because fund-suite growth creates more protocol-specific exceptions, and the operating model must scale without weakening control.', detail: 'Connects growth, complexity, and control.' },
              { label: 'Because AI can automate reconciliation.', detail: 'Overstates AI in a regulated workflow.' },
              { label: 'Because no-code tools are faster than engineering.', detail: 'Tool-first and weak on risk.' }
            ],
            correct: 1,
            explanation: 'The role exists because product growth changes the risk surface. That is the strategic frame.'
          }
        },
        {
          id: 'gi-arc',
          title: 'Answer Arc',
          why: {
            scenario: 'Under pressure, you may over-explain. The room needs a repeatable answer shape that works for product, architecture, risk, and leadership questions.',
            tension: 'A senior answer is structured enough to survive interruption.'
          },
          what: {
            definition: 'Four-beat answer',
            body: '**Context → risk → decision → proof.** Name the business situation, the risk or tradeoff, the product decision, and the measurable evidence that proves the decision worked.'
          },
          example: {
            label: 'Reusable answer spine',
            items: [
              { icon: '1', left: 'Context', right: 'Fund suite and operations are scaling.' },
              { icon: '2', left: 'Risk', right: 'Manual reconciliation hides freshness, ownership, and evidence gaps.' },
              { icon: '3', left: 'Decision', right: 'Prove one controlled workflow, then expand by risk.' },
              { icon: '4', left: 'Proof', right: 'Exception SLA, audit trail, source freshness, owner handoff.' }
            ]
          },
          drill: {
            type: 'match',
            question: 'Match each answer beat to the live sentence you would say.',
            pairs: [
              { item: 'Context', answer: 'The fund suite is scaling faster than manual operating patterns.' },
              { item: 'Risk', answer: 'A clean report is not enough if we cannot prove what was checked.' },
              { item: 'Decision', answer: 'I would prove the pattern on one high-risk workflow first.' },
              { item: 'Proof', answer: 'We measure freshness, exception SLA, audit evidence, and owner handoff.' }
            ],
            explanation: 'This is the shortest safe shape for most interview answers.'
          }
        }
      ]
    },
    {
      id: 'gi-s2-diana-ai',
      title: 'Diana + AI',
      subtitle: 'Bullish but disciplined',
      icon: 'AI',
      why: 'The prep notes flag Diana as especially interested in AI. You need a point of view that sounds current without putting probabilistic systems in the critical path of NAV-sensitive work.',
      concepts: [
        {
          id: 'gi-ai-thesis',
          title: 'AI Point of View',
          why: {
            scenario: 'Diana asks: "Where does AI belong in this workflow?" A generic "AI can summarize exceptions" answer will not be enough.',
            tension: 'You need to show AI fluency and regulated-product discipline at the same time.'
          },
          what: {
            definition: 'Best AI posture',
            body: '**Assistive, not authoritative.** Use AI for exception summaries, incident drafts, runbook suggestions, natural-language search over audit history, and anomaly triage. Keep authoritative state, reconciliation decisions, approvals, and audit evidence deterministic.'
          },
          what2: {
            definition: 'How to reconcile with "AI thin on purpose"',
            body: 'Say: "I am bullish on AI and use it daily, which is why I am disciplined about where it belongs. In a NAV-sensitive workflow, AI helps humans understand and act faster; it does not become the source of truth."'
          },
          drill: {
            type: 'choice',
            question: 'Which answer best handles Diana pressing for AI ambition?',
            options: [
              'I would let the model decide which exceptions matter so we can maximize automation.',
              'I would avoid AI because regulated products should stay deterministic.',
              'I would use AI assistively on top of deterministic controls: summaries, drafts, anomaly clusters, runbook suggestions, and audit-history search.',
              'I would replace no-code workflow with an agent.'
            ],
            correct: 2,
            explanation: 'This answer shows ambition and judgment. It names useful AI surfaces while protecting the control boundary.'
          }
        },
        {
          id: 'gi-ai-story',
          title: 'Personal AI Story',
          why: {
            scenario: 'She asks how you personally use AI. This is a fluency test, not a theoretical architecture question.',
            tension: 'You need a first-person story with outcome, not a tool list.'
          },
          what: {
            definition: 'Story shape',
            body: '**Problem → AI assist → human judgment → outcome.** Pick a real example where AI accelerated analysis, drafting, synthesis, prototyping, or debugging, then emphasize the review loop and measurable impact.'
          },
          example: {
            label: 'Answer components',
            items: [
              { icon: 'P', left: 'Problem', right: 'What decision or deliverable was blocked?' },
              { icon: 'A', left: 'AI assist', right: 'What did the model help draft, analyze, or explore?' },
              { icon: 'J', left: 'Judgment', right: 'How did you verify, constrain, or improve it?' },
              { icon: 'O', left: 'Outcome', right: 'What changed in time, quality, alignment, or risk?' }
            ]
          },
          drill: {
            type: 'scenario',
            question: 'You have 60 seconds to answer "How do you use AI personally?" Which structure should you use?',
            options: [
              { label: 'List tools and models you have tried.', detail: 'Shows exposure, not impact.' },
              { label: 'Describe one concrete workflow where AI accelerated a deliverable, then explain your verification loop and outcome.', detail: 'Shows fluency plus judgment.' },
              { label: 'Say AI is mostly hype but useful sometimes.', detail: 'Too defensive for this interviewer.' },
              { label: 'Explain transformer architecture.', detail: 'Too abstract for the question.' }
            ],
            correct: 1,
            explanation: 'A first-person workflow story is the safest proof of practical fluency.'
          }
        },
        {
          id: 'gi-ai-roadmap',
          title: 'Phase-Two AI Roadmap',
          why: {
            scenario: 'Diana asks what you would do after the deterministic base is live.',
            tension: 'The answer should sound like a roadmap, not a brainstorm.'
          },
          what: {
            definition: 'AI after the base',
            body: 'Once source data, ownership, and audit trails are reliable, AI can sit on top: summarize exceptions, detect recurring failure patterns, draft incident updates, recommend runbooks, and search historical resolutions. The prerequisite is trusted structured data.'
          },
          example: {
            label: 'Roadmap sequence',
            items: [
              { icon: '1', left: 'Foundation', right: 'Deterministic ingestion, state, workflow, audit evidence.' },
              { icon: '2', left: 'Assist', right: 'Summaries, search, drafts, runbook suggestions.' },
              { icon: '3', left: 'Measure', right: 'Time-to-triage, handoff quality, repeat exception reduction.' }
            ]
          },
          drill: {
            type: 'choice',
            question: 'What is the strongest reason to defer AI from the critical path at first?',
            options: [
              'The company probably does not have enough engineers.',
              'AI is not useful for operations.',
              'You need deterministic source-of-truth, audit, and escalation data before AI can safely improve the workflow.',
              'No-code tools cannot integrate with AI.'
            ],
            correct: 2,
            explanation: 'This frames sequencing as product maturity, not AI skepticism.'
          }
        }
      ]
    },
    {
      id: 'gi-s3-architecture',
      title: 'Architecture Defense',
      subtitle: 'Control boundary',
      icon: '▣',
      why: 'Vanessa and engineering will test whether the architecture is mature. Your goal is to prove that no-code accelerates workflow without becoming the hidden source of truth.',
      concepts: [
        {
          id: 'gi-boundary',
          title: 'Control Boundary',
          why: {
            scenario: 'Someone says: "Isn\'t no-code just tech debt?"',
            tension: 'If you cannot draw the boundary, the concern is valid.'
          },
          what: {
            definition: 'Boundary answer',
            body: '**RDS/S3 own truth and replayable evidence. No-code owns authenticated workflow, review queues, display, and approvals.** Business rules, schemas, mappings, and transformations are versioned outside the no-code surface.'
          },
          example: {
            label: 'Layer assignment',
            table: [
              { scenario: 'Immutable raw payloads', fix: 'S3/evidence layer', reason: 'Replayable and auditable.' },
              { scenario: 'Canonical state and mappings', fix: 'RDS/service layer', reason: 'Authoritative and queryable.' },
              { scenario: 'Analyst review queue', fix: 'No-code workflow', reason: 'Fast human action without hidden truth.' }
            ]
          },
          drill: {
            type: 'match',
            question: 'Put each responsibility in the correct layer.',
            pairs: [
              { item: 'Raw vendor payload', answer: 'Evidence layer' },
              { item: 'Canonical exception record', answer: 'Authoritative state' },
              { item: 'Approval screen', answer: 'Workflow layer' },
              { item: 'Schema transform code', answer: 'Controlled service layer' }
            ],
            explanation: 'The boundary is the defense against no-code overreach.'
          }
        },
        {
          id: 'gi-six-weeks',
          title: 'Six-Week Claim',
          why: {
            scenario: 'Engineering challenges the six-week timeline.',
            tension: 'You must avoid sounding like the whole platform is done in six weeks.'
          },
          what: {
            definition: 'What six weeks means',
            body: 'Six weeks means **one high-risk workflow live with real data, observable controls, audit trail, and reusable operating pattern**. It does not mean every asset, every vendor, every downstream workflow, or every AI idea is finished.'
          },
          drill: {
            type: 'scenario',
            question: 'How do you respond when someone says "Six weeks is unrealistic"?',
            options: [
              { label: 'Agree and remove the timeline.', detail: 'Loses product urgency.' },
              { label: 'Clarify that six weeks is one controlled workflow proving the pattern, not the whole platform.', detail: 'Protects ambition and credibility.' },
              { label: 'Say no-code makes anything possible.', detail: 'Sounds naive.' },
              { label: 'Promise more engineers.', detail: 'Not a product answer.' }
            ],
            correct: 1,
            explanation: 'Scope precision makes the timeline defensible.'
          }
        },
        {
          id: 'gi-chain-adapters',
          title: 'Chain-Specific Adapters',
          why: {
            scenario: 'A technical interviewer asks how Bitcoin, EVM, Solana, XRP/Stellar, Avalanche, and Sui fit one workflow.',
            tension: 'Flattening chain mechanics into fake sameness breaks downstream trust.'
          },
          what: {
            definition: 'Canonical envelope',
            body: 'Preserve chain-specific raw data, then normalize through explicit adapters into a canonical event envelope for downstream workflow. Keep extension fields for protocol-specific mechanics so shared workflow does not erase important differences.'
          },
          example: {
            label: 'Chain differences',
            table: [
              { scenario: 'Bitcoin', fix: 'UTXO model', reason: 'Outputs and confirmations matter.' },
              { scenario: 'EVM', fix: 'Accounts/events/logs', reason: 'Contract logs and token transfers need parsing.' },
              { scenario: 'Solana', fix: 'Accounts/programs/instructions', reason: 'High event volume and program parsing change ingestion.' }
            ]
          },
          drill: {
            type: 'choice',
            question: 'What is the safest architecture for multi-chain operations?',
            options: [
              'Create one generic transaction schema and discard chain-specific fields.',
              'Keep raw chain/vendor payloads immutable, then map through explicit adapters into canonical workflow events.',
              'Let each chain team build separate no-code apps.',
              'Only support EVM chains at first.'
            ],
            correct: 1,
            explanation: 'This preserves evidence and protocol specificity while giving operations a shared workflow surface.'
          }
        }
      ]
    },
    {
      id: 'gi-s4-risk',
      title: 'Risk + Controls',
      subtitle: 'Regulated-product posture',
      icon: '!',
      why: 'This is where you show maturity. The strongest product answer makes risk visible and operational, not abstract.',
      concepts: [
        {
          id: 'gi-data-risk',
          title: 'Feed Quality',
          why: {
            scenario: 'The workflow shows no exceptions. The interviewer asks: "How do you know nothing is wrong?"',
            tension: 'No exceptions only matters if you can prove the system checked the right records.'
          },
          what: {
            definition: 'Recon hubris',
            body: 'A clean queue is not proof. You need feed freshness, expected-record counts, schema validation, last-good-run, source status, and escalation rules for late, empty, or malformed data.'
          },
          drill: {
            type: 'choice',
            question: 'Which control best prevents "false clean" reporting?',
            options: [
              'Hide empty feeds so analysts are not distracted.',
              'Track source freshness, expected counts, schema validity, and last-good-run before declaring no exceptions.',
              'Ask vendors to email if anything breaks.',
              'Run AI anomaly detection first.'
            ],
            correct: 1,
            explanation: 'You need controls that prove the absence of exceptions is meaningful.'
          }
        },
        {
          id: 'gi-security',
          title: 'Security Review',
          why: {
            scenario: 'InfoSec asks what you need reviewed before production.',
            tension: 'A senior PM knows enough to invite the right review early.'
          },
          what: {
            definition: 'Production readiness review',
            body: 'Ask InfoSec and engineering to review data classification, access model, secrets, vendor posture, no-code admin permissions, logs, audit export, threat model, rollback, backup restore, and manual fallback.'
          },
          drill: {
            type: 'match',
            question: 'Match the review area to the reason it matters.',
            pairs: [
              { item: 'Data classification', answer: 'Prevents sensitive fields from leaking into workflow surfaces.' },
              { item: 'No-code admin model', answer: 'Prevents ungoverned permissions and hidden rule changes.' },
              { item: 'Backup restore testing', answer: 'Proves resilience is real, not documented only.' },
              { item: 'Vendor incident notice', answer: 'Controls dependency risk when source data changes.' }
            ],
            explanation: 'Security posture is a product constraint, not a late checklist.'
          }
        },
        {
          id: 'gi-vendors',
          title: 'Vendor Dependency',
          why: {
            scenario: 'A vendor changes a feed format on a Friday. Ops sees strange records Monday morning.',
            tension: 'Vendor monitoring is weak unless ownership, escalation, and evidence rights are explicit.'
          },
          what: {
            definition: 'Vendor-risk answer',
            body: 'Name SLAs, incident notice, format-change process, evidence rights, BCP/DR posture, contact path, and exit strategy. Tie each vendor dependency to an owner and escalation path.'
          },
          drill: {
            type: 'scenario',
            question: 'What should your first response be when a critical vendor feed is late or malformed?',
            options: [
              { label: 'Pause downstream automation, tag reports with data status, assess blast radius, and prepare the engineer/vendor handoff.', detail: 'Contains risk before diagnosis.' },
              { label: 'Wait for the vendor to resolve it.', detail: 'Too passive.' },
              { label: 'Let AI infer the missing records.', detail: 'Unsafe.' },
              { label: 'Ask analysts to manually override without tagging reports.', detail: 'Hides risk.' }
            ],
            correct: 0,
            explanation: 'Contain first, diagnose second. Make status visible and preserve evidence.'
          }
        }
      ]
    },
    {
      id: 'gi-s5-live-room',
      title: 'Live Pushback',
      subtitle: 'Answer under pressure',
      icon: 'Q',
      why: 'The interview will likely test how you think when challenged. Practice concise responses to the objections most likely to appear.',
      concepts: [
        {
          id: 'gi-finance',
          title: 'Finance Pushback',
          why: {
            scenario: 'Finance says: "This helps Ops, but what about us?"',
            tension: 'You need to show that the operating foundation creates a better source of truth for downstream teams.'
          },
          what: {
            definition: 'Finance answer',
            body: 'A better Ops control foundation helps Finance because downstream reporting inherits clearer source status, evidence, exception ownership, and reconciled state. Do not overpromise full Finance automation; identify which Finance needs the phase-one evidence already supports.'
          },
          drill: {
            type: 'choice',
            question: 'Which answer best handles Finance scope pressure?',
            options: [
              'Finance is out of scope, so I would not discuss it.',
              'I would add every Finance workflow to phase one.',
              'The Ops foundation improves the source of truth Finance depends on; then I would prioritize adjacent Finance needs by risk and reuse.',
              'Finance can use the no-code tool directly.'
            ],
            correct: 2,
            explanation: 'This acknowledges Finance without exploding scope.'
          }
        },
        {
          id: 'gi-culture',
          title: 'Culture Interview',
          why: {
            scenario: 'A senior leader barely discusses product and instead probes conflict, accountability, and what makes you tick.',
            tension: 'Do not force the conversation back to architecture.'
          },
          what: {
            definition: 'Culture posture',
            body: 'Be specific, accountable, and calm. Discuss failures without blaming former teams. Show coachability, principled tradeoffs, and how you communicate when the room is tense.'
          },
          drill: {
            type: 'scenario',
            question: 'You are asked about a past failure. What is the strongest structure?',
            options: [
              { label: 'Explain why stakeholders made the wrong call.', detail: 'Sounds defensive.' },
              { label: 'Name the goal, your miss, what you changed, and what you would do differently now.', detail: 'Shows accountability and learning.' },
              { label: 'Pivot to a success story.', detail: 'Avoids the question.' },
              { label: 'Keep it vague to avoid risk.', detail: 'Weak signal.' }
            ],
            correct: 1,
            explanation: 'Accountability without drama is the signal.'
          }
        },
        {
          id: 'gi-closing',
          title: 'Closing Questions',
          why: {
            scenario: 'You get the last five minutes. Your questions should make them imagine you in the role.',
            tension: 'Generic questions waste the highest-leverage part of the conversation.'
          },
          what: {
            definition: 'Strong question types',
            body: 'Ask about the operating model Diana is shaping, the highest-risk workflow to prove first, how Product partners with Ops/Finance/Engineering today, and what signals would make the first 90 days clearly successful.'
          },
          drill: {
            type: 'choice',
            question: 'Which closing question is strongest for Diana?',
            options: [
              'What is the work-life balance like?',
              'As you shape the operating model, where is the biggest gap between today\'s Ops workflow and what the fund suite needs at scale?',
              'What tools do you use?',
              'How soon can I be promoted?'
            ],
            correct: 1,
            explanation: 'It shows you understand her mandate and invites a strategic conversation.'
          }
        }
      ]
    },
    {
      id: 'gi-s6-90-days',
      title: 'First 90 Days',
      subtitle: 'Operating plan',
      icon: '90',
      why: 'A Principal PM should be able to turn the interview thesis into an execution plan with discovery, delivery, controls, and expansion.',
      concepts: [
        {
          id: 'gi-days-30',
          title: 'Days 1-30',
          why: {
            scenario: 'They ask: "What would you do first?"',
            tension: 'Do not start by building. Start by learning the operating truth.'
          },
          what: {
            definition: 'Discovery and trust',
            body: 'Map workflows, source systems, exception taxonomy, vendor dependencies, control requirements, stakeholder pain, and current metrics. Build trust with Ops, Finance, Engineering, Compliance, and InfoSec.'
          },
          drill: {
            type: 'match',
            question: 'Match the first-30-day activity to its output.',
            pairs: [
              { item: 'Workflow shadowing', answer: 'Actual exception paths and workarounds.' },
              { item: 'Source-system review', answer: 'Truth/evidence boundary.' },
              { item: 'Stakeholder map', answer: 'Decision owners and escalation paths.' },
              { item: 'Metric baseline', answer: 'Proof of improvement later.' }
            ],
            explanation: 'The first month produces shared facts and trust.'
          }
        },
        {
          id: 'gi-days-60',
          title: 'Days 31-60',
          why: {
            scenario: 'They ask how you avoid analysis paralysis.',
            tension: 'You need a narrow, real pilot with visible controls.'
          },
          what: {
            definition: 'Pilot the pattern',
            body: 'Pick one high-risk workflow. Define success metrics, source evidence, authoritative state, review queue, escalation, audit export, and manual fallback. Ship with the smallest credible scope.'
          },
          drill: {
            type: 'scenario',
            question: 'Which pilot scope is strongest?',
            options: [
              { label: 'Every reconciliation workflow across all funds.', detail: 'Too broad.' },
              { label: 'One high-risk, high-volume exception path with real source data and measurable controls.', detail: 'Focused and defensible.' },
              { label: 'A prototype with fake data.', detail: 'Too weak for operating proof.' },
              { label: 'A strategy deck only.', detail: 'Not enough delivery signal.' }
            ],
            correct: 1,
            explanation: 'The pilot must be narrow enough to ship and real enough to prove the operating model.'
          }
        },
        {
          id: 'gi-days-90',
          title: 'Days 61-90',
          why: {
            scenario: 'They ask how this becomes more than one workflow.',
            tension: 'Expansion should follow risk and reuse, not enthusiasm.'
          },
          what: {
            definition: 'Scale by pattern',
            body: 'Use pilot evidence to rank adjacent workflows by operational risk, exception volume, regulatory sensitivity, and reuse of the same source/state/workflow pattern. Publish the operating playbook and metric dashboard.'
          },
          drill: {
            type: 'choice',
            question: 'What is the best expansion principle after the pilot?',
            options: [
              'Expand to the loudest stakeholder first.',
              'Expand by risk, exception volume, regulatory sensitivity, and pattern reuse.',
              'Expand only to workflows with no engineering needs.',
              'Wait until the entire platform is rebuilt.'
            ],
            correct: 1,
            explanation: 'A Principal PM scales the pattern by value and risk, not by volume of requests.'
          }
        }
      ]
    }
  ]
};

const GRAYSCALE_PPM_MASTERY_LAB = {
  id: 'grayscale-ppm-mastery',
  title: 'Grayscale PPM Mastery',
  series: 'Principal PM Mastery Lab',
  level: 3,
  moduleLabel: 'B',
  description: 'Deep mastery course for Grayscale context: digital asset products, fund operations, chain mechanics, architecture, strategy, and Principal PM leadership.',
  tags: ['web3', 'funds', 'architecture', 'strategy', 'leadership'],
  stages: [
    {
      id: 'gm-s1-business',
      title: 'Business Context',
      subtitle: 'How Grayscale makes money',
      icon: '$',
      why: 'You need enough company and market fluency to connect product decisions to revenue, trust, fee pressure, and fund flows.',
      concepts: [
        {
          id: 'gm-aum',
          title: 'AUM Fee Model',
          why: { scenario: 'An interviewer asks how Grayscale makes money and why product operations matter.', tension: 'Do not answer like an exchange PM.' },
          what: { definition: 'Revenue model', body: 'Grayscale primarily earns management fees on assets under management. That is steadier than transaction-fee revenue, but it still moves with crypto prices, flows, fee pressure, and investor trust.' },
          drill: { type: 'choice', question: 'What is the product implication of AUM-based revenue?', options: ['Volume spikes matter more than trust.', 'Operational trust, product breadth, and retention matter because revenue follows managed assets.', 'Fees are unrelated to product quality.', 'Only trading speed matters.'], correct: 1, explanation: 'AUM economics make trust, product breadth, reliability, and investor confidence central product concerns.' }
        },
        {
          id: 'gm-etp',
          title: 'ETP / Fund Operations',
          why: { scenario: 'The discussion moves from product strategy to daily fund operations.', tension: 'Senior PMs must connect investor product promises to operational machinery.' },
          what: { definition: 'Operating chain', body: 'Fund products depend on custody, valuation, creation/redemption processes, index or oracle inputs, fund admin workflows, disclosures, and exception handling. Product quality includes the reliability of that operating chain.' },
          drill: { type: 'match', question: 'Match each function to the product risk it controls.', pairs: [
            { item: 'Custody', answer: 'Asset safeguarding and access policy.' },
            { item: 'Fund admin', answer: 'Accounting, NAV, and reporting workflow.' },
            { item: 'Index/oracle input', answer: 'Pricing and valuation signal.' },
            { item: 'Exception workflow', answer: 'Timely escalation and evidence.' }
          ], explanation: 'Fund product work is operationally cross-functional by nature.' }
        },
        {
          id: 'gm-trust',
          title: 'Trust as Product Surface',
          why: { scenario: 'A product idea looks attractive but creates opaque operational risk.', tension: 'The product surface includes what clients never see directly.' },
          what: { definition: 'Trust surface', body: 'In regulated asset management, trust is built by custody posture, reporting reliability, operational evidence, incident response, disclosures, and the ability to prove what happened.' },
          drill: { type: 'scenario', question: 'Which metric best complements ordinary delivery velocity?', options: [
            { label: 'Number of screens shipped.', detail: 'Useful but incomplete.' },
            { label: 'Exception age, source freshness, audit completeness, and time-to-owner.', detail: 'Measures operating trust.' },
            { label: 'Number of roadmap themes.', detail: 'Too abstract.' },
            { label: 'Number of AI features.', detail: 'Not a trust metric.' }
          ], correct: 1, explanation: 'For Grayscale, operating reliability is part of the product.' }
        }
      ]
    },
    {
      id: 'gm-s2-digital-assets',
      title: 'Digital Asset Mechanics',
      subtitle: 'Where traditional finance assumptions break',
      icon: '₿',
      why: 'Traditional finance concepts still apply, but custody, finality, staking, and chain data differ enough to create product risk.',
      concepts: [
        {
          id: 'gm-finality',
          title: 'Finality and Calendars',
          why: { scenario: 'You reconcile on-chain movement with traditional banking rails.', tension: 'One side runs 24/7 with probabilistic or protocol-specific finality; the other runs on business calendars.' },
          what: { definition: 'Mismatch', body: 'On-chain settlement, bank settlement, fund accounting, and reporting can operate on different clocks and finality assumptions. Reconciliation must handle pending, confirmed, reversed, delayed, and calendar-bound states.' },
          drill: { type: 'choice', question: 'Why is on-chain/bank reconciliation difficult?', options: ['On-chain has no records.', 'Different finality models and calendars collide.', 'Banks never use APIs.', 'Crypto always settles slower.'], correct: 1, explanation: 'The hard part is mismatched finality and time, not absence of data.' }
        },
        {
          id: 'gm-custody',
          title: 'Custody Tiers',
          why: { scenario: 'Someone asks why the fund cannot keep everything in cold storage.', tension: 'Security and operational liquidity trade off.' },
          what: { definition: 'Tiered custody', body: 'Cold storage protects assets but reduces operational accessibility. A mature posture uses policy-governed tiers: cold for the bulk, warm/hot only where operational liquidity requires it, with access controls and evidence.' },
          drill: { type: 'scenario', question: 'What is the strongest answer to "Why not keep everything cold?"', options: [
            { label: 'Cold storage is always best.', detail: 'Too simplistic.' },
            { label: 'Pure cold can break redemption/service needs; pure hot is too risky. Use policy-governed tiers.', detail: 'Names the tradeoff.' },
            { label: 'Hot wallets are easier.', detail: 'Unsafe.' },
            { label: 'The custodian decides everything.', detail: 'Outsources product judgment.' }
          ], correct: 1, explanation: 'The senior answer names security, liquidity, policy, and control.' }
        },
        {
          id: 'gm-staking',
          title: 'Staking Product Risk',
          why: { scenario: 'A staking-related product decision creates operational questions.', tension: 'Yield mechanics add validator, slashing, liquidity, tax/accounting, and disclosure complexity.' },
          what: { definition: 'Staking dimensions', body: 'Staking is not just yield. It introduces validator selection, lockups, slashing risk, reward accounting, governance, network-specific operations, disclosures, and client expectation management.' },
          drill: { type: 'match', question: 'Match staking risk to product concern.', pairs: [
            { item: 'Slashing', answer: 'Loss/risk disclosure and validator diligence.' },
            { item: 'Lockup', answer: 'Liquidity and redemption planning.' },
            { item: 'Rewards', answer: 'Accounting and reporting treatment.' },
            { item: 'Validator dependency', answer: 'Vendor/third-party risk management.' }
          ], explanation: 'Staking product work is operational and risk-heavy.' }
        }
      ]
    },
    {
      id: 'gm-s3-architecture',
      title: 'Operating Architecture',
      subtitle: 'From source data to confidence',
      icon: '▤',
      why: 'The architecture story should prove that every downstream decision can be traced to source data, controlled state, and human ownership.',
      concepts: [
        {
          id: 'gm-ingress',
          title: 'Ingress and Evidence',
          why: { scenario: 'A vendor payload changes shape and downstream reports still look normal.', tension: 'Without source evidence and schema checks, normal-looking output can hide broken input.' },
          what: { definition: 'Ingress contract', body: 'Authenticated payloads, schema validation, idempotency, source freshness, immutable raw storage, and replay capability are the foundation. Never let the display layer be the first place a feed problem appears.' },
          drill: { type: 'choice', question: 'What is the most important raw-data principle?', options: ['Overwrite old payloads to save space.', 'Preserve immutable raw payloads so records can be replayed and audited.', 'Only store normalized records.', 'Store only screenshots.'], correct: 1, explanation: 'Immutable evidence lets the team reconstruct what happened.' }
        },
        {
          id: 'gm-canonical',
          title: 'Canonical Event Model',
          why: { scenario: 'Every chain and vendor has different semantics.', tension: 'A shared workflow needs stable concepts without pretending all protocols are identical.' },
          what: { definition: 'Canonical plus extensions', body: 'Normalize into shared event concepts for workflow while preserving protocol-specific extension fields. Raw payload remains available for replay, debugging, and audit.' },
          drill: { type: 'scenario', question: 'Which canonical model approach is strongest?', options: [
            { label: 'Flatten everything to the smallest common schema.', detail: 'Loses important mechanics.' },
            { label: 'Shared envelope plus protocol-specific extensions and raw evidence.', detail: 'Balances consistency and fidelity.' },
            { label: 'One workflow per chain forever.', detail: 'Does not scale.' },
            { label: 'Only parse data manually.', detail: 'Too slow and brittle.' }
          ], correct: 1, explanation: 'This is the scalable middle path.' }
        },
        {
          id: 'gm-human-workflow',
          title: 'Human-in-the-Loop Workflow',
          why: { scenario: 'An approval may take three days.', tension: 'Do not hold a running execution open or bury ownership in chat.' },
          what: { definition: 'Task-token / callback posture', body: 'Long-running human review should pause cleanly, assign ownership, preserve evidence, and resume on callback or state change. The product experience is the queue, SLA, evidence, and escalation path.' },
          drill: { type: 'choice', question: 'How should a multi-day human approval be modeled?', options: ['Hold an open execution for days.', 'Pause with task/callback state, owner, SLA, and evidence.', 'Ask the analyst to email Engineering.', 'Let AI approve it.'], correct: 1, explanation: 'The workflow should pause without losing state or accountability.' }
        }
      ]
    },
    {
      id: 'gm-s4-strategy',
      title: 'Product Strategy',
      subtitle: 'Prioritize by risk and reuse',
      icon: '◇',
      why: 'A Principal PM must turn a broad problem space into a few defensible bets that executives can support.',
      concepts: [
        {
          id: 'gm-prioritization',
          title: 'Risk-Weighted Prioritization',
          why: { scenario: 'Ten teams want workflow improvements at once.', tension: 'The loudest request is not necessarily the right first bet.' },
          what: { definition: 'Priority formula', body: 'Prioritize by operational risk, NAV/reporting sensitivity, exception volume, stakeholder pain, feasibility, and reuse of the operating pattern. Make tradeoffs explicit.' },
          drill: { type: 'match', question: 'Match priority signal to why it matters.', pairs: [
            { item: 'NAV sensitivity', answer: 'Financial/reporting impact.' },
            { item: 'Exception volume', answer: 'Operational leverage.' },
            { item: 'Pattern reuse', answer: 'Platform scalability.' },
            { item: 'Feasibility', answer: 'Time-to-proof.' }
          ], explanation: 'This gives you a defensible roadmap conversation.' }
        },
        {
          id: 'gm-metrics',
          title: 'Executive Metrics',
          why: { scenario: 'Executives ask how they will know the product is working.', tension: 'Adoption alone is not enough.' },
          what: { definition: 'Metric set', body: 'Use exception SLA, source freshness, time-to-owner, audit completeness, manual rework reduction, incident rate, and adjacent workflow reuse. Pair speed metrics with control metrics.' },
          drill: { type: 'choice', question: 'Which metric set best fits this product?', options: ['Page views and button clicks only.', 'Exception SLA, source freshness, audit completeness, rework reduction, and owner handoff.', 'Number of dashboards.', 'Model token usage.'], correct: 1, explanation: 'The metrics must prove operating confidence, not just UI activity.' }
        },
        {
          id: 'gm-roadmap',
          title: 'Roadmap Narrative',
          why: { scenario: 'You need to align Ops, Finance, Engineering, Compliance, and executives.', tension: 'Different stakeholders care about different proof points.' },
          what: { definition: 'Narrative', body: 'Tell the roadmap as an operating maturity curve: prove one workflow, harden controls, expand adjacent workflows by risk/reuse, then layer assistive AI on trusted data.' },
          drill: { type: 'scenario', question: 'Which roadmap story is strongest?', options: [
            { label: 'Ship many screens quickly.', detail: 'Activity, not maturity.' },
            { label: 'Prove one controlled workflow, harden, expand by risk/reuse, then add assistive AI.', detail: 'Clear maturity path.' },
            { label: 'Wait for a full platform rewrite.', detail: 'Too slow.' },
            { label: 'Use AI first to show innovation.', detail: 'Bad sequencing.' }
          ], correct: 1, explanation: 'This is a strategic story executives can sponsor.' }
        }
      ]
    },
    {
      id: 'gm-s5-leadership',
      title: 'Principal PM Leadership',
      subtitle: 'Influence without authority',
      icon: '↑',
      why: 'This role may require raising product craft without direct reports. You need to show senior influence, not just individual execution.',
      concepts: [
        {
          id: 'gm-craft',
          title: 'Raise Product Craft',
          why: { scenario: 'You are asked how you mentor PMs without managing them.', tension: 'Influence comes from making the better way easier, not from title.' },
          what: { definition: 'Craft leadership', body: 'Model high-quality artifacts, run critique forums, provide reusable templates, ask sharper questions, share credit, and make the better product practice visible and easier to adopt.' },
          drill: { type: 'choice', question: 'How does a Principal PM raise team craft without authority?', options: ['Ask for approval rights over every roadmap.', 'Model the behavior, provide templates, convene critique, and credit others.', 'Escalate weak PMs immediately.', 'Avoid mentoring because it is not formal management.'], correct: 1, explanation: 'Influence spreads through artifacts, forums, questions, and credit.' }
        },
        {
          id: 'gm-conflict',
          title: 'Cross-Functional Conflict',
          why: { scenario: 'Ops wants speed, Compliance wants controls, Engineering wants clean architecture.', tension: 'You cannot win by picking one group and dismissing the others.' },
          what: { definition: 'Conflict posture', body: 'Name the real tradeoff, anchor on customer/business risk, separate reversible and irreversible decisions, and facilitate a decision with clear owner, rationale, and follow-up metric.' },
          drill: { type: 'scenario', question: 'What is the strongest move in a tense cross-functional disagreement?', options: [
            { label: 'Push your preferred solution harder.', detail: 'May escalate tension.' },
            { label: 'Name the tradeoff and decision criteria, then drive to owner/rationale/metric.', detail: 'Senior facilitation.' },
            { label: 'Defer all decisions to Engineering.', detail: 'Abdicates product role.' },
            { label: 'Schedule another meeting without a decision path.', detail: 'Stalls.' }
          ], correct: 1, explanation: 'Principal PMs make decision quality better under ambiguity.' }
        },
        {
          id: 'gm-head-path',
          title: 'Path to Head Role',
          why: { scenario: 'The role could evolve into broader product leadership.', tension: 'You should sound ambitious but grounded in the seat in front of you.' },
          what: { definition: 'Ambition frame', body: 'Say you are excited by the Principal mandate because it lets you create the operating pattern, build trust, raise product craft, and earn broader scope through measurable impact.' },
          drill: { type: 'choice', question: 'How should you discuss ambition for a future Head role?', options: ['Ask when the promotion happens.', 'Avoid ambition entirely.', 'Show that you will earn broader scope by delivering the Principal mandate and raising the operating/product standard.', 'Say you only want strategy, not execution.'], correct: 2, explanation: 'This is ambitious without sounding entitled.' }
        }
      ]
    }
  ]
};

const WEB3_SECURITY_FOUNDATION_LAB = {
  id: 'web3-security-foundation',
  title: 'Web3 + Security Foundation',
  series: 'Principal PM Foundation Lab',
  level: 2,
  moduleLabel: 'C',
  description: 'A practical foundation for Web3 product interviews: chain models, custody, key management, threat modeling, vendor/feed risk, secure SDLC, and regulated AI boundaries.',
  tags: ['web3', 'security', 'custody', 'risk', 'sdlc'],
  stages: [
    {
      id: 'ws-s1-chain-basics',
      title: 'Chain Basics',
      subtitle: 'Settlement, state, and finality',
      icon: '⛓',
      why: 'You do not need protocol-engineer depth, but you need enough chain fluency to ask good questions and avoid generic fintech assumptions.',
      concepts: [
        {
          id: 'ws-finality',
          title: 'Finality Models',
          why: { scenario: 'A report depends on whether a transfer is final, pending, or reversible.', tension: 'Different chains and rails settle differently.' },
          what: { definition: 'Finality', body: 'Finality is the confidence that a transaction will not be reversed. Some systems feel deterministic; others are probabilistic or protocol-specific. Product workflows need explicit states such as pending, confirmed, stale, disputed, and reconciled.' },
          drill: { type: 'choice', question: 'What should a product workflow do with finality uncertainty?', options: ['Hide it from users.', 'Represent state explicitly and gate downstream actions until confidence is sufficient.', 'Assume all chains settle instantly.', 'Let analysts decide without evidence.'], correct: 1, explanation: 'State modeling turns protocol uncertainty into controlled workflow behavior.' }
        },
        {
          id: 'ws-chain-models',
          title: 'Chain Data Models',
          why: { scenario: 'You are comparing Bitcoin, EVM, Solana, XRP/Stellar, Avalanche, and Sui.', tension: 'A transaction is not the same product object everywhere.' },
          what: { definition: 'Model differences', body: '**Bitcoin** uses UTXOs. **EVM** uses accounts, contracts, logs, and events. **Solana** uses accounts, programs, and instructions. Payment ledgers and object-centric chains introduce their own semantics. A good product model preserves differences at ingress and normalizes only what workflow needs.' },
          drill: { type: 'match', question: 'Match the chain concept to the product parsing concern.', pairs: [
            { item: 'UTXO', answer: 'Track outputs, spends, and confirmations.' },
            { item: 'EVM logs', answer: 'Parse contract events and token transfers.' },
            { item: 'Solana instructions', answer: 'Interpret program/account-level actions.' },
            { item: 'Object-centric chain', answer: 'Track object state transitions.' }
          ], explanation: 'This vocabulary helps you sound precise without overclaiming protocol depth.' }
        },
        {
          id: 'ws-reconciliation',
          title: 'On-Chain Reconciliation',
          why: { scenario: 'On-chain, custodian, fund admin, and internal workflow records disagree.', tension: 'The product question is not "which screen is right?" but "what evidence decides?"' },
          what: { definition: 'Reconciliation foundation', body: 'Strong reconciliation keeps immutable source evidence, normalized state, expected counts, freshness checks, exception ownership, and audit trail. The workflow should explain why records disagree and who owns resolution.' },
          drill: { type: 'scenario', question: 'Which evidence set is strongest for a reconciliation exception?', options: [
            { label: 'Analyst note only.', detail: 'Not enough evidence.' },
            { label: 'Raw source payloads, normalized record, freshness check, owner, timestamp, and resolution note.', detail: 'Replayable and accountable.' },
            { label: 'Screenshot of the dashboard.', detail: 'Weak and hard to audit.' },
            { label: 'AI-generated summary without source links.', detail: 'Useful assistively, not authoritative.' }
          ], correct: 1, explanation: 'Security and auditability depend on evidence lineage.' }
        }
      ]
    },
    {
      id: 'ws-s2-custody-keys',
      title: 'Custody + Keys',
      subtitle: 'How assets are protected',
      icon: '🔐',
      why: 'Custody is where product, security, operations, and client trust meet. You need clear language around keys, access, tiers, and operational liquidity.',
      concepts: [
        {
          id: 'ws-key-risk',
          title: 'Private Key Risk',
          why: { scenario: 'An interviewer asks why digital asset custody is different from ordinary account permissions.', tension: 'Private keys are bearer-control assets; misuse can be irreversible.' },
          what: { definition: 'Key management', body: 'Private keys control asset movement. Mature custody uses segregation, hardware security modules or dedicated custody infrastructure, multi-party approval, least privilege, policy controls, logging, and break-glass procedures.' },
          drill: { type: 'choice', question: 'What makes private-key risk especially severe?', options: ['Keys are easy to reset.', 'Unauthorized signing can move assets irreversibly.', 'Keys are only passwords.', 'Key risk is unrelated to product.'], correct: 1, explanation: 'The product workflow must respect the severity of signing authority.' }
        },
        {
          id: 'ws-multisig-mpc',
          title: 'Multi-Sig and MPC',
          why: { scenario: 'Someone asks how custody systems reduce single-person risk.', tension: 'You need the concept without pretending to design cryptography live.' },
          what: { definition: 'Shared control', body: 'Multi-signature and MPC-style custody patterns reduce single-key/single-person risk by requiring multiple approvals or distributed signing participation. Product workflows should model approval policy, signer roles, thresholds, evidence, and exception paths.' },
          drill: { type: 'match', question: 'Match the control to the risk it reduces.', pairs: [
            { item: 'Threshold approval', answer: 'Single actor compromise.' },
            { item: 'Signer role separation', answer: 'Conflict of interest or excessive privilege.' },
            { item: 'Immutable signing log', answer: 'Weak audit trail.' },
            { item: 'Break-glass procedure', answer: 'Emergency access without chaos.' }
          ], explanation: 'The interview signal is knowing what product must capture around custody controls.' }
        },
        {
          id: 'ws-hot-warm-cold',
          title: 'Hot, Warm, Cold',
          why: { scenario: 'A fund needs both safety and operational movement capability.', tension: 'Pure cold and pure hot are both bad product answers.' },
          what: { definition: 'Tiered access', body: 'Cold storage maximizes safety but limits speed. Hot access maximizes liquidity but expands attack surface. Warm tiers and policy-based movement balance operations and security. Product must make tier, authority, rationale, and evidence visible.' },
          drill: { type: 'scenario', question: 'Which custody posture is strongest?', options: [
            { label: 'Everything hot for speed.', detail: 'Too risky.' },
            { label: 'Everything cold forever.', detail: 'May break operations.' },
            { label: 'Policy-governed tiers with thresholds, approvals, logs, and operational rationale.', detail: 'Balanced and controllable.' },
            { label: 'Analysts decide case by case without policy.', detail: 'Inconsistent and weak.' }
          ], correct: 2, explanation: 'Good product security is controlled flexibility.' }
        }
      ]
    },
    {
      id: 'ws-s3-threat-model',
      title: 'Threat Model',
      subtitle: 'Where systems fail',
      icon: '!',
      why: 'A security foundation should help you identify likely failures before a security reviewer has to drag them out of you.',
      concepts: [
        {
          id: 'ws-attack-surface',
          title: 'Attack Surface',
          why: { scenario: 'You are launching a workflow that ingests vendor feeds and exposes review queues.', tension: 'Every integration and role creates a place to fail.' },
          what: { definition: 'Surface map', body: 'Map identity, admin roles, vendor endpoints, secrets, webhooks, file uploads, no-code permissions, logs, AI prompts, source data, and export paths. For each, ask: who can access it, change it, spoof it, or exfiltrate it?' },
          drill: { type: 'match', question: 'Match surface to primary concern.', pairs: [
            { item: 'Webhook endpoint', answer: 'Spoofing and replay.' },
            { item: 'No-code admin role', answer: 'Excessive permissions and hidden rule changes.' },
            { item: 'Logs', answer: 'Sensitive data exposure.' },
            { item: 'Secrets', answer: 'Credential theft and unauthorized access.' }
          ], explanation: 'Threat modeling starts with naming the surfaces.' }
        },
        {
          id: 'ws-secure-sdlc',
          title: 'Secure SDLC',
          why: { scenario: 'Engineering asks what security practices you expect before production.', tension: 'You should know enough to partner, not enough to pretend you are the security owner.' },
          what: { definition: 'Security partnership', body: 'Secure SDLC includes threat modeling, code review, dependency scanning, secrets scanning, IaC review, approval gates, rollback plans, access reviews, audit logging, and incident tabletop exercises.' },
          drill: { type: 'choice', question: 'Which answer best describes your PM role in Secure SDLC?', options: ['Delegate all security to engineering.', 'Define product risk, ensure reviews happen early, make tradeoffs visible, and track launch-blocking controls.', 'Personally approve every code change.', 'Skip reviews for a pilot.'], correct: 1, explanation: 'A Principal PM makes security part of product delivery without pretending to own every technical control.' }
        },
        {
          id: 'ws-ai-boundary',
          title: 'AI Security Boundary',
          why: { scenario: 'The team wants to use AI in exception triage.', tension: 'Prompt injection and hallucination matter when source data influences operational action.' },
          what: { definition: 'AI control boundary', body: 'Use AI for assistive summarization, clustering, drafts, and search. Do not let it authoritatively reconcile, approve, mutate source records, or bypass evidence. Protect prompts, source citations, reviewer confirmation, and audit logs.' },
          drill: { type: 'scenario', question: 'Where is AI safest in a regulated operations workflow?', options: [
            { label: 'Critical-path approval.', detail: 'Too much authority.' },
            { label: 'Assistive summary with source links and human confirmation.', detail: 'Useful and bounded.' },
            { label: 'Direct database mutation.', detail: 'Unsafe.' },
            { label: 'Replacing audit logs.', detail: 'Invalid control.' }
          ], correct: 1, explanation: 'AI should accelerate understanding, not become the source of truth.' }
        }
      ]
    },
    {
      id: 'ws-s4-operational-risk',
      title: 'Operational Risk',
      subtitle: 'Feeds, vendors, incidents',
      icon: '◇',
      why: 'Most product failures in this space are not spectacular hacks; they are late feeds, unclear owners, bad permissions, stale evidence, and silent assumptions.',
      concepts: [
        {
          id: 'ws-feed-controls',
          title: 'Feed Controls',
          why: { scenario: 'A feed is empty but no exception appears.', tension: 'Empty input can masquerade as a clean output.' },
          what: { definition: 'Feed control set', body: 'Track expected records, freshness, schema version, last-good-run, checksum or signature when available, vendor status, and downstream blast radius. Escalate late/empty/malformed feeds explicitly.' },
          drill: { type: 'choice', question: 'What prevents an empty feed from looking like no exceptions?', options: ['Only count displayed exceptions.', 'Expected-count and freshness checks before declaring clean state.', 'AI guessing missing rows.', 'Manual review once a month.'], correct: 1, explanation: 'Absence of evidence is not evidence of absence.' }
        },
        {
          id: 'ws-vendor-risk',
          title: 'Vendor Risk',
          why: { scenario: 'A critical provider changes API behavior without notice.', tension: 'Your product is only as reliable as its dependency management.' },
          what: { definition: 'Vendor posture', body: 'Track SLAs, format-change notice, incident contacts, data rights, BCP/DR evidence, exit plan, support path, and monitoring. Make vendor dependency visible in roadmap and incident planning.' },
          drill: { type: 'match', question: 'Match vendor control to why it matters.', pairs: [
            { item: 'Format-change notice', answer: 'Prevents silent parser breakage.' },
            { item: 'Incident contact path', answer: 'Speeds escalation.' },
            { item: 'Data/evidence rights', answer: 'Supports audit and replay.' },
            { item: 'Exit plan', answer: 'Reduces lock-in risk.' }
          ], explanation: 'Vendor risk is product risk when vendor data drives operations.' }
        },
        {
          id: 'ws-incident',
          title: 'Incident Response',
          why: { scenario: 'Bad data may have affected a report.', tension: 'The first move is containment, not root-cause theater.' },
          what: { definition: 'Incident sequence', body: 'Establish facts, assess blast radius, contain downstream use, tag affected reports, preserve evidence, assign owner, communicate status, then diagnose and prevent recurrence.' },
          drill: { type: 'scenario', question: 'What is the best first response to suspected bad source data?', options: [
            { label: 'Root cause fully before telling anyone.', detail: 'Too slow.' },
            { label: 'Contain, tag status, preserve evidence, assign owner, and assess blast radius.', detail: 'Correct incident posture.' },
            { label: 'Delete questionable records.', detail: 'Destroys evidence.' },
            { label: 'Let the dashboard stay green until confirmed.', detail: 'Hides risk.' }
          ], correct: 1, explanation: 'Containment and evidence preservation come before deep diagnosis.' }
        }
      ]
    }
  ]
};

const LIBRARY_COURSES = [
  GRAYSCALE_INTERVIEW_PREP_LAB,
  GRAYSCALE_PPM_MASTERY_LAB,
  WEB3_SECURITY_FOUNDATION_LAB
];

const SUGGESTED_NEXT = [
  {
    title: 'Run the live interview gauntlet',
    reason: 'After you master the interview prep module, cycle through Diana/AI, architecture, risk, and culture answers until each one fits a crisp 60-90 second arc.',
    prereq: 'grayscale-interview-prep',
    level: 3,
    moduleLabel: 'A',
  },
  {
    title: 'Deepen digital asset operating fluency',
    reason: 'The mastery module gives you the fintech/Web3 vocabulary to defend architecture and strategy without sounding generic.',
    prereq: 'grayscale-ppm-mastery',
    level: 3,
    moduleLabel: 'B',
  },
  {
    title: 'Build Web3 + security foundations',
    reason: 'This course gives you the custody, chain, threat-model, and secure-SDLC language to handle technical and risk-oriented interview loops.',
    prereq: 'web3-security-foundation',
    level: 2,
    moduleLabel: 'C',
  },
];

window.LAB_CONFIG = {
  brand: 'Grayscale Lab',
  title: 'Grayscale interview courses',
  description: 'Practice the Principal PM story, deepen digital-asset operating fluency, and build the Web3/security foundation behind the interview loop.',
  eyebrow: 'Principal PM Interview Lab',
  nextEyebrow: 'Start here',
  nextTitle: 'Begin with the interview module',
  nextBody: 'The interview prep course is the highest-leverage path this week: thesis, Diana/AI, architecture defense, risk controls, live pushback, and first-90-day plan.',
  nextCourseId: 'grayscale-interview-prep',
  nextCta: 'Start interview prep →',
};
window.LIBRARY_COURSES = LIBRARY_COURSES;
window.SUGGESTED_NEXT = SUGGESTED_NEXT;
