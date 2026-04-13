# Agentic System Design & Design Patterns: From Zero to Platform Architect

A comprehensive course for experienced software engineers entering the world of agentic AI — covering everything from LLM fundamentals to designing production-grade agent platforms. 149 named design patterns, each with a software engineering parallel.

## Who This Is For

- Tech leaders with deep backend/distributed systems experience (microservices, message queues, databases, caching, load balancing)
- Strong conceptual fluency with GoF patterns, CQRS, event sourcing, and systems thinking
- Zero prior knowledge of LLMs, agents, or agentic AI required — true 0-to-1
- Goal: architect AI-native platforms at the level of Claude Code, Cursor, or Devin

## Prerequisites

- Strong background in backend systems, distributed computing, and software architecture
- Familiarity with design patterns (GoF, CQRS, event sourcing)
- Basic understanding of APIs, databases, and CI/CD
- No AI/ML/LLM knowledge required

## How to Use

Work through the modules in order — each builds on the previous. Every module includes:
- **Software engineering parallels** to anchor every new concept in something you know
- **Named design patterns** taught in context with trade-offs and concrete scenarios
- **Key takeaways** (3-5 per module)
- **Try This** — a hands-on exercise using Claude, GPT, or open-source models
- **System Design Question** — a mini whiteboard problem you should now be able to answer

Estimated total reading time: ~4 hours. Allow 8-12 hours including exercises.

## Learning Path

### Part 1: Foundations (3 modules, ~35 min reading)

| Module | Title | Time | Focus |
|--------|-------|------|-------|
| 01 | What LLMs Actually Are | 11 min | Tokens, context windows, knowledge types, transformer constraints |
| 02 | The Economics of Inference | 12 min | Prefill/decode costs, prompt caching, build vs. buy |
| 03 | From Prompting to Programming | 11 min | System prompts, few-shot, structured output, prompt composition |

### Part 2: Single Agent (4 modules, ~51 min reading)

| Module | Title | Time | Patterns |
|--------|-------|------|----------|
| 04 | Anatomy of an Agent | 12 min | Agent architecture: 6 subsystems, tool cycle, stop conditions |
| 05 | Reasoning Patterns | 12 min | 8 patterns: ReAct, CoT, ToT, GoT, LATS, Plan-Then-Execute, Self-Discover, Inference-Time Scaling |
| 06 | Tool Use Patterns | 13 min | 19 patterns: tool design, code execution, selection/routing, specialized capabilities |
| 07 | Memory, Context & State | 14 min | 17 patterns: context budget, injection, memory tiers, state persistence |

### Part 3: Multi-Agent (4 modules, ~41 min reading)

| Module | Title | Time | Patterns |
|--------|-------|------|----------|
| 08 | Why Multi-Agent | 9 min | 5 patterns: routing, Dual LLM, budget-aware routing, escalation, agent modes |
| 09 | Orchestration Architectures | 11 min | 9 patterns: orchestrator-worker, sub-agents, map-reduce, factory, IoC, hybrid workflows |
| 10 | Communication & Coordination | 10 min | 11 patterns: ensemble, debate, best-of-N, contracts, saga coordination, swarm migration |
| 11 | Advanced Orchestration | 11 min | 11 patterns: autonomous loops, state machines, background agents, distributed workers |

### Part 4: Feedback & Learning (2 modules, ~23 min reading)

| Module | Title | Time | Patterns |
|--------|-------|------|----------|
| 12 | Feedback Loops | 12 min | 10 patterns: reflection, self-critique, CI feedback, eval synthesis, reward shaping |
| 13 | Learning & Adaptation | 11 min | 10 patterns: prompt refinement, Agent RFT, skill libraries, MemRL, compounding engineering |

### Part 5: Production Hardening (3 modules, ~32 min reading)

| Module | Title | Time | Patterns |
|--------|-------|------|----------|
| 14 | Reliability Engineering | 12 min | 12 patterns: schema enforcement, observability, RLAIF, canary rollout, grader design |
| 15 | Security & Safety | 11 min | 11 patterns: sandboxing, egress lockdown, PII tokenization, zero-trust, Lethal Trifecta |
| 16 | Cost, Scaling & Operations | 9 min | 5 patterns: no-token-limit, sandbox scaling, async pipelines, coherence sessions |

### Part 6: Agent Platform (3 modules, ~30 min reading)

| Module | Title | Time | Focus |
|--------|-------|------|-------|
| 17 | Agent Runtime Architecture | 10 min | Reverse-engineering Claude Code: 5 runtime layers |
| 18 | Building Developer Platforms | 10 min | SDK design, multi-tenancy, tool ecosystems, hooks, extension points |
| 19 | Eval Infrastructure at Scale | 10 min | Eval pipeline: case management, parallel execution, grading, deploy gates |

### Part 7: UX & Collaboration (2 modules, ~21 min reading)

| Module | Title | Time | Patterns |
|--------|-------|------|----------|
| 20 | Interaction Patterns | 10 min | 8 patterns: human-in-the-loop, spectrum of control, streaming, scaffolding |
| 21 | Team & Organizational Patterns | 11 min | 8 patterns: config-as-code, codebase optimization, democratization, funding |

### Part 8: Capstone (2 modules, ~19 min reading)

| Module | Title | Time | Focus |
|--------|-------|------|-------|
| 22 | End-to-End Platform Design | 10 min | Full system design exercise integrating patterns from every part |
| 23 | The Evolving Landscape | 9 min | Durable vs. transitional patterns, emerging frontiers, what to build now |

## Architect Partner Skill

An architecture partner skill that uses retrieval-first design to brainstorm, review, and stress-test your agentic system designs against the 149 patterns in this course. Instead of preloading the full course, it routes your query through the course index and pulls only the most relevant modules and excerpts.

Interaction modes: **Pattern Recommendation**, **Design Review**, **Solution Exploration**, **Devil's Advocate**.

See [agentic-systems-architect/README.md](agentic-systems-architect/README.md) for installation and usage instructions.

## Supporting Materials

- **[glossary.md](glossary.md)** — 55+ terms defined with module of first introduction
- **[patterns-index.md](patterns-index.md)** — All 149 patterns with the module where each is taught

## By the Numbers

- **23 modules** across 8 parts
- **149 named design patterns**, each with an SE parallel
- **~50,000 words** of technical content
- **~4 hours** estimated reading time (8-12 hours with exercises)
- **0 prerequisites** in AI/ML — starts from absolute zero
