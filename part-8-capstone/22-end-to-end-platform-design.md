# Module 22: End-to-End Platform Design

**Software engineering parallel**: The system design interview — you're given an open-ended requirement and must design a complete architecture on a whiteboard, making trade-offs explicit, referencing known patterns, and defending your decisions. This module is that exercise for an agent platform.

**Patterns covered**: None new (capstone module — integrates patterns from all prior modules into a complete design)

---

## The Exercise

Design a production agent platform — "Codex" — that enables a 200-person engineering organization to use AI coding agents for daily development work. The platform must support interactive use (developer at a terminal), background processing (CI-triggered agents), and autonomous operation (issue queue processing).

This is the system design interview you should be able to whiteboard after completing this course. Every architectural decision references a pattern you've learned. Every trade-off has been discussed in a prior module.

## Requirements

**Functional requirements**:
- Developers can invoke agents interactively from their IDE or terminal
- Agents can read, write, and search code; run tests and builds; create PRs
- Agents can be triggered by events (GitHub push, Jira ticket, cron schedule)
- Multiple agents can work on the same codebase concurrently
- The platform accumulates knowledge about each project and developer over time

**Non-functional requirements**:
- 200 developers, peak 50 concurrent sessions
- Average session: 30 turns, 20K input tokens per turn, 1K output tokens per turn
- 99.5% availability target
- Per-session cost should average under $3 for routine tasks
- Security: SOC 2 compliant, no data leaves the organization's approved boundaries

## Layer 1: Inference Infrastructure

**Decision: Hybrid model deployment** (Module 2)

Run three model tiers:
- **Frontier** (Opus-class via API): Complex reasoning, architecture, planning. ~$15/M input, ~$75/M output.
- **Mid-tier** (Sonnet-class via API): General coding, implementation, review. ~$3/M input, ~$15/M output.
- **Fast** (Haiku-class, self-hosted): Classification, routing, formatting, simple edits. ~$0.25/M input, ~$1.25/M output.

Self-host the fast tier on internal GPU infrastructure. At 200 developers, the volume justifies the fixed cost — the break-even point (Module 2) for a Haiku-class model at this usage is approximately 2 weeks of API pricing.

**Router** (Router Agent / Model Selection, Module 8): A fast model classifies each task by difficulty and routes to the appropriate tier. Progressive Complexity Escalation (Module 8): start cheap, escalate on failure. Budget-Aware Model Routing (Module 8): each session has a $5 default budget, adjustable per team.

**Cost estimate**: 200 developers × 20 sessions/day × $3/session average = $12,000/day = ~$260K/month. With prompt caching (Module 7) achieving 70% hit rate on static content, effective cost drops to ~$180K/month.

## Layer 2: Agent Runtime

**Session Manager** (Module 17):
- Sessions are identified by user + project + session_id
- State stored in Redis during active session (conversation history, working memory)
- Persisted to PostgreSQL on session end (archive memory, metrics)
- Session timeout: 2 hours idle, 8 hours maximum

**Prompt Compositor** (Module 17):
```
Composition order:
1. Base system prompt (global)                    [CACHED — shared across org]
2. Tool definitions (per-project)                 [CACHED — shared per project]
3. Project context: CLAUDE.md, repo structure     [CACHED — shared per project]
4. Team configuration (per-team)                  [CACHED — shared per team]
5. Developer preferences (per-user)               [SEMI-CACHED]
6. Memory injection: relevant archive memories    [DYNAMIC]
7. Conversation history                           [DYNAMIC — grows per turn]
8. Working memory: todo list, tracked files       [DYNAMIC]
```

Layers 1-4 are static across many sessions → prompt cache hit rate of ~60-70%. This is the Prompt Caching via Exact Prefix Preservation pattern (Module 7) and Layered Configuration Context (Module 7) working together.

**Tool Registry** (Module 4):
Core tools: `read_file`, `edit_file`, `glob`, `grep`, `bash`, `write_file`
Project tools: loaded per-project via MCP configuration (Code Mode MCP Tool Interface, Module 6)
Tool steering: system prompt includes guidance on when to use each tool (Tool Use Steering via Prompting, Module 6)

**Context Management**:
- Context-Minimization (Module 7): read functions not files, include only relevant context per step
- Auto-Compaction (Module 7): trigger at 80% context utilization, summarize older turns
- Progressive Disclosure (Module 7): show file structure first, load specific sections on demand
- Working Memory via TodoWrite (Module 7): structured task tracking that survives compaction

## Layer 3: Execution Infrastructure

**Sandbox Pool** (Adaptive Sandbox Fan-Out Controller, Module 16):
- Container-based sandboxes using lightweight VMs (Firecracker or gVisor)
- Pool size: min 20 pre-warmed, max 100, auto-scale based on queue depth
- Per-sandbox limits: 2 CPU, 4GB RAM, 50GB disk, 30-minute timeout
- Workspace: git worktree per sandbox (workspace sync handled by git)

**Isolation** (Module 15):
- Filesystem: sandbox sees only the project workspace, read-only access to system libraries
- Network: Egress Lockdown — allow-list of approved endpoints (LLM API, package registries, internal git server). No arbitrary outbound connections.
- Credentials: External Credential Sync via HashiCorp Vault. Credentials injected at tool execution time, never in the LLM context.
- Resource: Hard CPU/memory/time limits. Non-Custodial Spending Controls enforced by the runtime, not the prompt.

**Concurrency** (Workspace-Native Multi-Agent Orchestration, Module 11):
Each agent session works on its own git branch. An orchestration layer prevents merge conflicts:
- Before starting work, check if another agent has an active branch touching the same files
- If conflict detected: queue the second task, or assign a different scope
- On completion: automated merge with conflict detection. If conflict, spawn a merge agent or escalate to human.

## Layer 4: Quality Infrastructure

**Eval Pipeline** (Module 19):
- Eval suite: 500+ cases. 200 regression (from incidents), 150 capability, 100 adversarial, 50+ per-team custom.
- Execution: nightly full run (all 500 cases × 3 runs each = 1,500 executions). On prompt change: targeted run (relevant subset, ~100 cases). On model change: full run.
- Grading: test-based for code correctness, rule-based for style/security, LLM-judge for holistic quality. Calibrated against human judgments quarterly.
- Deploy gates: block deployment if pass rate drops >3% vs. baseline.

**Feedback Loops** (Module 12):
- CI Feedback Loop: agent runs tests after every code change, reads failures, iterates
- Self-Critique Evaluator Loop: structured rubric scoring before presenting output
- Incident-to-Eval Synthesis: every production failure becomes a new eval case within 24 hours

**Observability** (LLM Observability, Module 14):
- Per-request metrics: tokens, latency, model used, cost
- Per-session dashboards: total cost, turns, tool usage, outcome
- Anomaly detection: alert on cost spikes (agent looping), error rate increases, latency degradation
- Cost attribution: tagged by team, project, and developer for chargeback (Module 16)

## Layer 5: Platform Services

**Authentication & Authorization**:
- SSO integration with the org's identity provider
- Per-user, per-team, per-project permission policies
- Sandboxed Tool Authorization (Module 15): each user's agent runs with that user's permissions — no privilege escalation

**Event System** (Module 18):
- Multi-Platform Webhook Triggers: GitHub pushes → code review agent, Jira ticket creation → triage agent, cron schedule → tech debt scanner
- Multi-Platform Communication Aggregation: agent results delivered via Slack, GitHub PR comments, or Jira updates — based on team configuration
- Internal event bus (Redis Streams): agent-to-agent communication, progress events, completion callbacks

**Memory System** (Hierarchical Memory, Module 7):
- **Working memory** (L1): Redis, per-session. Current conversation, active task state. Evicted on session end.
- **Main memory** (L2): PostgreSQL, per-session. Compacted conversation history, retrieved via semantic search. Retained for 30 days.
- **Archive memory** (L3): Filesystem (Filesystem-Based Agent State, Module 7) stored in the repo as `.agent/` directory. Per-project knowledge, developer preferences. Version-controlled. Persists indefinitely.

Self-Identity Accumulation (Module 7): after each session, extract key learnings about the project and developer. Inject at session start to bootstrap context.

## Layer 6: Developer Experience

**Interfaces**:
- CLI tool (primary): `codex "fix the failing test in auth.py"`. Streams agent reasoning, shows tool calls, supports interruption (Chain-of-Thought Monitoring & Interruption, Module 20).
- IDE extension: inline agent invocation from the editor. Abstracted Code Representation (Module 20) — changes shown as diffs with annotations.
- Background mode: `codex --background "update all API error handlers"`. Seamless Background-to-Foreground Handoff (Module 20) when human input is needed.

**Configuration** (Team-Shared Agent Configuration as Code, Module 21):
```
repo/
├── .agent/
│   ├── config.yml          # Project-level agent configuration
│   ├── memory/             # Persistent project knowledge
│   └── skills/             # Project-specific skill templates
├── CLAUDE.md               # Project context for the agent
```

All version-controlled. Teams customize agent behavior via PR.

**Autonomy Model** (Spectrum of Control, Module 20):
Default: Confirm mode (agent proposes, human approves writes). Developers can opt into Autonomous-with-Review for trusted projects. Background agents run in Autonomous mode with Milestone Escrow (Module 21): budget released in increments tied to verified progress (tests pass, lint clean, PR created).

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                    Clients                           │
│  CLI  │  IDE Extension  │  Webhook Gateway  │  Cron │
└───┬───┴────────┬────────┴─────────┬─────────┴───┬───┘
    │            │                  │              │
    ▼            ▼                  ▼              ▼
┌─────────────────────────────────────────────────────┐
│              API Gateway / Load Balancer             │
├─────────────────────────────────────────────────────┤
│              Session Manager (Redis)                 │
├──────────┬──────────┬───────────┬───────────────────┤
│  Prompt  │  Model   │   Tool    │   Memory          │
│  Comp.   │  Router  │  Engine   │   Manager         │
├──────────┴──────────┴───────────┴───────────────────┤
│              Sandbox Pool (Firecracker)              │
├─────────────────────────────────────────────────────┤
│  Vault  │  Event Bus  │  Eval Pipeline  │  Metrics  │
└─────────┴─────────────┴─────────────────┴───────────┘
```

## Trade-Off Summary

| Decision | Alternative | Why this choice |
|----------|------------|-----------------|
| Hybrid model (API + self-hosted) | Pure API | Volume justifies self-hosting for fast tier; frontier via API for flexibility |
| Container sandboxes | Full VMs | Faster startup, cheaper; sufficient isolation for code execution |
| Git worktrees for concurrency | File locking | Familiar model, natural conflict detection, leverages git tooling |
| Redis for session state | PostgreSQL only | Sub-millisecond reads for active sessions; PG for persistence |
| Filesystem-based archive memory | Vector DB | Simple, version-controllable, human-readable; vector DB adds complexity without clear benefit at this scale |
| Nightly full eval runs | On-every-change | 500 cases × 3 runs is expensive; nightly balances cost and freshness |

## Key Takeaways

1. The platform is six layers: inference infrastructure, agent runtime, execution infrastructure, quality infrastructure, platform services, and developer experience. Each layer has independent scaling and failure modes.
2. Cost management is architectural: prompt caching (60-70% hit rate), model routing (3 tiers), progressive escalation, and budget controls combine to bring average session cost under $3.
3. Security is defense-in-depth: sandboxed execution, egress lockdown, credential isolation, permission policies, and non-custodial spending controls — no single layer failure compromises the system.
4. Quality is a flywheel: eval suite grows from incidents, grading calibrates against humans, deploy gates prevent regressions, feedback loops improve agents continuously.
5. Every architectural decision maps to a named pattern from this course — the patterns aren't academic; they're the building blocks of the system you just designed.

## Try This

Take the Codex design above and adapt it for a different scale:
1. **Startup (10 developers)**: What layers can you skip? What simplifications make sense? (Hint: skip self-hosted models, use a single model tier, simplify the eval pipeline.)
2. **Enterprise (2,000 developers)**: What breaks at 10× scale? Where do you need horizontal scaling? What new concerns emerge? (Hint: multi-region, team-level eval suites, dedicated model capacity.)

For each scale, identify: which patterns become more important, which become less important, and which new patterns (or pattern combinations) emerge.

## System Design Question

A competitor launches a similar platform but with a key difference: they use a single frontier model for everything (no routing, no tiers). Their pitch is "simpler architecture, best quality on every task." Counter their design: what are the scaling, cost, and reliability weaknesses of their approach? At what usage level does their cost model break? How would you design a competitive response that matches their quality while maintaining your cost advantage?
