# Module 18: Building Developer Platforms

**Software engineering parallel**: Platform engineering — building the tools, SDKs, APIs, and extension points that other developers use to build their own applications. The difference between a product (you use it) and a platform (others build on it).

**Patterns covered**: Multi-Platform Communication Aggregation, Multi-Platform Webhook Triggers

---

## From Agent to Platform

Module 17 covered the runtime — the engine that executes a single agent. This module covers the platform layer on top: the infrastructure that lets developers build, configure, deploy, and operate their own agents using your runtime as a foundation.

The distinction is critical. Claude Code is an agent. The Anthropic API + Agent SDK + MCP ecosystem is a platform. Cursor is an agent. The extension system that lets developers add custom commands and context providers is a platform feature. The highest-value work in agentic AI isn't building individual agents — it's building the infrastructure that makes building agents easy.

**SE parallel**: The progression from application to platform mirrors every major technology wave. Salesforce went from CRM app to development platform (Force.com). AWS went from internal infrastructure to cloud platform. Stripe went from payments API to financial infrastructure platform. In each case, the platform became more valuable than any single application built on it.

## The Platform Stack

A developer-facing agent platform has four layers:

```
┌─────────────────────────────────────────┐
│  Layer 4: Developer Experience          │
│  CLI tools, documentation, templates,   │
│  debugging tools, local dev environment │
├─────────────────────────────────────────┤
│  Layer 3: Extension Points              │
│  Custom tools, MCP servers, hooks,      │
│  prompt libraries, skill registries     │
├─────────────────────────────────────────┤
│  Layer 2: Platform Services             │
│  Authentication, multi-tenancy,         │
│  billing, storage, event bus            │
├─────────────────────────────────────────┤
│  Layer 1: Agent Runtime (Module 17)     │
│  Session management, tool execution,    │
│  sandbox orchestration, model routing   │
└─────────────────────────────────────────┘
```

Module 17 covered Layer 1. This module covers Layers 2-4.

## Layer 2: Platform Services

### Multi-Tenancy

Multiple users and organizations share the same infrastructure. This requires:

**Isolation**: Each tenant's agents, data, memory, and configuration must be isolated from other tenants. This goes beyond sandbox isolation (Module 15) — it includes: separate memory stores, separate tool configurations, separate billing accounts, and separate audit logs.

**Resource governance**: Per-tenant rate limits, budget caps (Non-Custodial Spending Controls, Module 15), and priority levels. Tenant A's spike in usage must not degrade Tenant B's experience.

**Configuration scoping**: Settings exist at multiple levels — platform defaults, organization settings, project settings, user settings. The platform must resolve these correctly (Layered Configuration Context, Module 7) and let administrators at each level manage their scope.

**SE parallel**: Multi-tenant SaaS architecture. Every SaaS platform (Slack, GitHub, Datadog) solves the same problems: tenant isolation, resource governance, and hierarchical configuration. Agent platforms add the twist that tenants' agents can execute arbitrary code — making isolation harder and more important.

### Pattern: Multi-Platform Communication Aggregation

**What it does**: Provides a unified message bus that connects agents to multiple communication platforms (Slack, GitHub, email, Jira, Teams) through a single abstraction.

**SE parallel**: Unified message bus / integration middleware. Enterprise integration platforms (MuleSoft, Zapier, n8n) aggregate communication channels behind a unified API. Multi-Platform Communication Aggregation does the same for agents: the agent sends a "notification" message, and the platform routes it to the right channel based on configuration.

**How it works**: Define a canonical message format:
```
{
  "type": "code_review_complete",
  "severity": "info",
  "title": "PR #142 review complete",
  "body": "Found 2 issues: ...",
  "actions": [{"label": "View PR", "url": "..."}],
  "routing": {"channel": "engineering", "mention": "@alice"}
}
```

The platform translates this into Slack messages, GitHub PR comments, Jira ticket updates, or email — based on the organization's configuration. The agent never needs to know which communication platform is in use.

**Why it matters**: Without aggregation, every agent must be built with specific integrations for each platform. Adding Microsoft Teams support means modifying every agent. With aggregation, adding Teams support is a single platform change that all agents benefit from immediately.

### Pattern: Multi-Platform Webhook Triggers

**What it does**: Enables agents to be triggered by events from external platforms — a GitHub push, a Jira ticket creation, a Slack message, a cron schedule — through a unified event ingestion system.

**SE parallel**: Event-driven architecture / webhook gateway. An API gateway that receives webhooks from diverse sources, normalizes them into a standard event format, and routes them to the appropriate handler. Multi-Platform Webhook Triggers does this for agent activation.

**How it works**:
```
External Event → Webhook Endpoint → Event Normalizer → Router → Agent

Example flows:
  GitHub push to main       → trigger: code review agent
  Jira ticket created (P0)  → trigger: bug triage agent
  Slack message "@agent fix" → trigger: coding agent
  Cron: daily at 2am        → trigger: tech debt scanner
```

Each trigger type has: an event schema, validation rules, authentication (verify the webhook is genuine), and routing logic (which agent handles this event type).

**Why it matters for platforms**: Triggers are how agents go from interactive tools to automated infrastructure. Without triggers, every agent invocation requires a human typing a command. With triggers, agents react to events autonomously — the coding platform becomes an event-driven system where agents are the handlers.

### Event Bus and Async Communication

Beyond triggers, the platform needs internal eventing:

- **Agent-to-agent communication**: Orchestrator agents dispatch work to sub-agents via the event bus, not via direct coupling. This enables scaling and replacement of agent implementations without changing the orchestration logic (Inversion of Control, Module 9).
- **Status and progress events**: Long-running agents publish progress events that the UI subscribes to. The user sees "Reading files... Analyzing... Writing code..." without polling.
- **Completion callbacks**: When a background agent finishes (Background Agent with CI Feedback, Module 12), the event bus delivers the result to the user's session, notification channel, or downstream workflow.

**SE parallel**: This is pub-sub (Kafka, RabbitMQ, Redis Streams) applied to agent coordination. The event bus decouples producers (agents generating results) from consumers (UIs, other agents, webhook endpoints). The same decoupling patterns — at-least-once delivery, dead letter queues, consumer groups — apply.

## Layer 3: Extension Points

### Tool Ecosystem

The platform's value grows with the number of tools available. Building a tool ecosystem requires:

**Tool registry**: A catalog of available tools with metadata — name, description, schema, author, version, usage statistics, quality ratings. Developers publish tools; agents discover them (Progressive Tool Discovery, Module 6).

**Tool packaging**: A standard format for distributing tools. MCP (Module 6) provides the protocol; the platform provides the packaging: how to declare dependencies, how to specify resource requirements, how to bundle configuration.

**Tool marketplace**: Quality signal for third-party tools. Which tools are popular? Which have high success rates? Which are well-maintained? This is npm for agent tools — and it needs the same infrastructure: version management, deprecation policies, security scanning, and trust signals.

**SE parallel**: Package registries (npm, PyPI, crates.io) + plugin marketplaces (VS Code extensions, WordPress plugins). The platform provides the registry infrastructure; the community provides the tools.

### Prompt and Skill Libraries

Beyond tools, the platform can host reusable prompts and skills (Skill Library Evolution, Module 13):

**Prompt templates**: Reusable prompt components that developers can compose into their agents. A "code review" prompt template, a "security analysis" skill template — published, versioned, and quality-rated.

**Configuration templates**: Pre-built agent configurations for common use cases. "Python web development agent" bundles a system prompt, tool set, memory configuration, and testing strategy that works well for Python web projects. Developers start from the template and customize.

### Hook System

Hooks let developers inject custom behavior at defined points in the agent lifecycle without modifying the runtime:

```
Hook Points:
  session.start     → Load custom context, initialize integrations
  tool.pre_execute  → Custom authorization, logging, transformation
  tool.post_execute → Result filtering, PII scrubbing, metrics
  model.pre_call    → Prompt modification, token budgeting
  model.post_call   → Output filtering, quality scoring
  session.end       → Cleanup, state persistence, reporting
```

Each hook receives the relevant context (tool call, model response, session state) and can: modify it, log it, reject it, or pass it through. Hooks are the primary mechanism for enterprises to enforce custom policies without forking the runtime.

**SE parallel**: Git hooks, CI pipeline hooks, Kubernetes admission webhooks. Every extensible system provides lifecycle hooks. The agent platform's hook system is how security teams enforce scanning (Deterministic Security Scanning Build Loop, Module 15), how compliance teams enforce PII rules (PII Tokenization, Module 15), and how individual teams customize agent behavior.

## Layer 4: Developer Experience

### SDK Design

The Agent SDK (Module 6) is how developers programmatically build agents. Good SDK design principles:

**Progressive complexity**: Simple things should be simple; complex things should be possible.
```python
# Simple: one-liner agent
result = agent.run("Fix the failing test in auth.py")

# Intermediate: configured agent
agent = Agent(
    model="claude-sonnet-4-6",
    tools=[read_file, edit_file, run_tests],
    system_prompt=load("prompts/coding.md"),
    max_turns=30
)
result = agent.run(task)

# Advanced: full control
agent = Agent(config)
agent.on("tool.pre_execute", my_auth_hook)
agent.on("model.post_call", my_quality_scorer)
for turn in agent.stream(task):
    handle_turn(turn)
```

**Typed interfaces**: Every SDK method should have full type definitions — autocomplete guides developers through the API without reading docs. Tool schemas, response types, and configuration options should all be typed.

**Sensible defaults**: The SDK should work well with zero configuration. Default model selection, default tools, default memory management, default stop conditions — all set to reasonable values that work for 80% of use cases.

### Local Development Environment

Developers need to test agents locally before deploying:

**Local runtime**: A lightweight version of the production runtime that runs on a developer's machine. Same session management, same tool execution, same prompt composition — but against a local workspace with mock or real model calls.

**Replay and debugging**: Record an agent session (all messages, tool calls, tool results) and replay it deterministically. Change the prompt and replay to see how the change affects behavior. Step through the agent's decisions turn by turn, inspecting context at each point.

**SE parallel**: Local development servers (Django's `runserver`, Next.js `dev`). The local environment should be as close to production as possible, with fast iteration and debuggability. The replay capability is analogous to deterministic replay in distributed systems debugging.

### Documentation and Examples

**Reference docs**: Auto-generated from SDK types and tool schemas. Every method, every parameter, every configuration option documented with types and examples.

**Tutorials**: Step-by-step guides for common use cases: "Build a code review agent," "Add a custom tool," "Configure memory for a large codebase."

**Example agents**: Production-quality reference implementations that developers can read, run, and adapt. Not toy examples — real agents that handle real tasks, demonstrating best practices.

## Key Takeaways

1. The platform stack has four layers: runtime (Module 17), platform services (multi-tenancy, event bus, billing), extension points (tools, hooks, skills), and developer experience (SDK, local dev, docs).
2. Multi-Platform Communication Aggregation unifies outbound messaging so agents work with any communication channel through a single abstraction.
3. Multi-Platform Webhook Triggers unify inbound events so agents can be triggered by any external system — turning agents from interactive tools into event-driven automation.
4. The tool ecosystem (registry, packaging, marketplace) determines the platform's long-term value — it's npm for agent capabilities.
5. SDK design follows progressive complexity: simple things simple, complex things possible. Typed interfaces, sensible defaults, and full lifecycle hooks.

## Try This

Design a tool package format:
1. Define what a tool package must contain: manifest (name, version, description, author), schema (JSON Schema for parameters), implementation (code or MCP endpoint), and configuration (required secrets, dependencies).
2. Write three tool packages: a file search tool, a database query tool, and a notification sender.
3. Design the registry API: publish, search, install, version, and deprecate.
4. Consider: How do you handle tool versioning when the schema changes? How do you test tools for quality? How do you handle a tool that becomes a security risk?

This exercise teaches platform thinking — you're building infrastructure that other developers consume.

## System Design Question

You're designing a developer platform for agent-powered code review. The platform must support: 50 engineering teams, each with custom review rules; integration with GitHub, GitLab, and Bitbucket; custom tools for accessing internal documentation and compliance databases; and a skill library where teams share reusable review strategies. Design the platform architecture: How do you structure multi-tenancy (per-team isolation with shared infrastructure)? How do you handle the three VCS integrations (communication aggregation and webhook triggers)? How do you design the extension points so teams can customize review behavior without modifying the core runtime?
