# Course Index: Agentic System Design & Design Patterns

> **For LLM agents**: You are reading an index of a 23-module course on agentic AI system design. This course teaches 149 named design patterns for building AI agent systems, written for experienced software engineers with zero prior AI/ML knowledge. Every agentic concept is grounded in a software engineering parallel.
>
> **How to use this index**:
> - If you have a **problem to solve** → scan the Problem Clusters section. Each cluster groups patterns by the problem archetype they address. This is your fastest path.
> - If you need **deeper understanding** of a specific module → read its entry in Module Details. Each entry explains what mental models the module builds.
> - If you encounter an **unfamiliar term** → check the Glossary at the end. Every term is defined with its SE parallel.
> - If a module summary is insufficient → fetch the full file at the listed path.
> - **Dependencies matter**: modules build on earlier modules. Check the `builds_on` field before reading a module in isolation.

---

## Course Structure

```
part-1-foundations/     Modules 1-3    What LLMs are, how inference economics work, prompt-as-code
part-2-single-agent/    Modules 4-7    Agent anatomy, reasoning, tool use, memory & context
part-3-multi-agent/     Modules 8-11   When/why multi-agent, orchestration, coordination, autonomy
part-4-feedback-learning/ Modules 12-13  Feedback loops, learning, adaptation, meta-patterns
part-5-production/      Modules 14-16  Reliability, security, cost, scaling, operations
part-6-platform/        Modules 17-19  Runtime architecture, developer platforms, eval infrastructure
part-7-ux/              Modules 20-21  Human-agent interaction, team adoption
part-8-capstone/        Modules 22-23  End-to-end platform design, evolving landscape
```

---

## Problem Clusters: Pattern → Module Routing

Each cluster represents a problem archetype. Patterns are listed with their SE parallel and the module where they are taught. The cluster description tells you when this group of patterns is relevant.

---

### Your agent can't reason through complex problems

You need the agent to think harder, explore alternatives, or match reasoning depth to task difficulty.

| Pattern | SE Parallel | Module |
|---------|-------------|--------|
| Chain-of-Thought | Debug logging / showing your work | 5 |
| ReAct — Reason + Act | OODA loop | 5 |
| Plan-Then-Execute | Query planner + executor in databases | 5 |
| Tree-of-Thought | Branch-and-bound algorithms | 5 |
| Graph of Thoughts | DAG-based workflow engines | 5 |
| Self-Discover | Runtime query plan optimization | 5 |
| LATS (Language Agent Tree Search) | Monte Carlo Tree Search | 5 |
| Inference-Time Scaling | Horizontal autoscaling / compute-on-demand | 5 |

Start with ReAct (the default). Escalate to Plan-Then-Execute for multi-step tasks. Tree/Graph reasoning costs 10-100x more — use only when solution space needs exploration.

---

### Your agent needs to discover and select tools at runtime

The agent has access to many tools and must choose the right one, or tools should be revealed progressively to avoid context bloat.

| Pattern | SE Parallel | Module |
|---------|-------------|--------|
| LLM-Friendly API Design | Developer experience in API design | 6 |
| Dual-Use Tool Design | APIs serving humans and machines | 6 |
| Shell Command Contextualization | man pages / --help | 6 |
| Progressive Tool Discovery | Service discovery / DNS | 6 |
| Code Mode MCP Tool Interface | gRPC + protobuf | 6 |
| Agent SDK for Programmatic Control | Client SDKs | 6 |
| Action-Selector Pattern | Strategy / command pattern | 6 |
| Tool Use Steering via Prompting | Hinting query optimizers | 6 |
| Patch Steering via Prompted Tool Selection | Content-based routing | 6 |

Tool descriptions must say *when* to use the tool, not just *what* it does. Progressive Discovery is critical — injecting all tools upfront wastes context and confuses selection.

---

### Your agent needs to execute code safely

The agent writes and runs code as its primary action language, or needs to execute shell commands intelligently.

| Pattern | SE Parallel | Module |
|---------|-------------|--------|
| Code-Then-Execute | Compile-and-run / REPL | 6 |
| CodeAct Agent | Stored procedures / server-side scripting | 6 |
| Dynamic Code Injection | Hot module replacement / plugins | 6 |
| Code-Over-API | Stored procedures vs API calls | 6 |
| Intelligent Bash Tool Execution | Smart build systems | 6 |
| CLI-Native Agent Orchestration | Unix philosophy | 6 |
| CLI-First Skill Design | Composable CLI tools | 6 |
| Conditional Parallel Tool Execution | async.parallel with guards | 6 |

CodeAct is maximally flexible but requires strong sandboxing. Prefer constrained tool calls for production; reserve code execution for development agents.

---

### Your agent needs to search and retrieve external information

The agent must access knowledge beyond its training data — documents, codebases, the web, or visual content.

| Pattern | SE Parallel | Module |
|---------|-------------|--------|
| RAG — Retrieval-Augmented Generation | Cache-aside / read-through cache + search index | 7 |
| Agentic Search Over Vector Embeddings | Inverted + vector indices | 6 |
| Visual AI Multimodal Integration | Multi-format content pipelines | 6 |
| Agent-Powered Codebase Q&A / Onboarding | Documentation-as-code / code search indices | 7 |
| AI Web Search Agent Loop | Web crawler architecture | 19 |

RAG is the foundational pattern — it bridges the knowledge cutoff. Vector search adds semantic retrieval. Multimodal extends beyond text.

---

### Your agent's context window is filling up

Context is the agent's RAM. You need to manage what's in it, compress what's old, and cache what's reusable.

| Pattern | SE Parallel | Module |
|---------|-------------|--------|
| Context-Minimization Pattern | Payload optimization / lean DTOs | 7 |
| Context Window Auto-Compaction | Buffer pool eviction / LRU cache | 7 |
| Progressive Disclosure for Large Files | Pagination / streaming responses | 7 |
| Semantic Context Filtering | Query optimization / index selection | 7 |
| Prompt Caching via Exact Prefix Preservation | HTTP cache / CDN edge caching | 7 |
| Curated Code/File Context Window | Selective cache warming | 7 |
| Dynamic Context Injection | Lazy loading / dependency injection | 7 |
| Layered Configuration Context | Hierarchical config (env vars > config file > defaults) | 7 |
| No-Token-Limit Magic | Pagination + streaming | 16 |

Context-Minimization is highest-impact — every token costs O(n^2) in attention. Prompt Caching (exact prefix match) saves ~90% on input costs. No-Token-Limit composes several patterns to handle unbounded work.

---

### Your agent needs memory across turns or sessions

The agent must remember what happened earlier in the conversation, across sessions, or accumulate identity over time.

| Pattern | SE Parallel | Module |
|---------|-------------|--------|
| Hierarchical Memory — Working/Main/Archive | CPU cache hierarchy L1/L2/L3 | 7 |
| Working Memory via TodoWrite | In-process task queues | 7 |
| Episodic Memory Retrieval & Injection | Event sourcing / audit logs | 7 |
| Memory Synthesis from Execution Logs | Log aggregation → dashboards | 7 |
| Self-Identity Accumulation | Session affinity / sticky sessions | 7 |
| Filesystem-Based Agent State | Persistent state on disk / WAL | 7 |
| Proactive Agent State Externalization | Checkpointing in distributed systems | 7 |

Three-tier memory mirrors hardware: working memory (context window — fast, small), main memory (session-scoped — compacted out but retrievable), archive (persistent across sessions — filesystem/database).

---

### A single agent can't handle the task — you need routing or escalation

The task exceeds one model's capability, or you need cost-efficient model selection.

| Pattern | SE Parallel | Module |
|---------|-------------|--------|
| Router Agent / Model Selection | Reverse proxy / intelligent load balancer | 8 |
| Dual LLM Pattern | Backend-for-Frontend (BFF) pattern | 8 |
| Budget-Aware Model Routing with Hard Cost Caps | Rate limiting + tiered pricing | 8 |
| Progressive Complexity Escalation | Tiered escalation | 8 |
| Agent Modes by Model Personality | Runtime profiles | 8 |

Router Agent is foundational — classify task, route to cheapest capable model. Dual LLM (smart planner + cheap executor) saves 60-80% on typical workloads.

---

### You need to coordinate multiple agents on a shared task

Multiple agents must decompose work, execute in parallel, and synthesize results.

| Pattern | SE Parallel | Module |
|---------|-------------|--------|
| Orchestrator-Worker | Master-worker in distributed computing | 9 |
| Planner-Worker Separation | Control plane vs data plane | 9 |
| Sub-Agent Spawning | Fork/exec, thread pools | 9 |
| Oracle and Worker Multi-Model Approach | Coordinator-worker | 9 |
| LLM Map-Reduce Pattern | MapReduce / Spark | 9 |
| Factory over Assistant | Factory pattern in OOP | 9 |
| Inversion of Control | IoC/DI, Hollywood principle | 9 |
| Hybrid LLM/Code Workflow Coordinator | Airflow | 9 |
| Discrete Phase Separation | SEDA architecture | 9 |

Orchestrator-Worker is the default topology. Sub-Agent Spawning solves context exhaustion (fresh windows for subtasks). Hybrid LLM/Code is most cost-effective — use deterministic code for predictable steps, agents only for reasoning.

---

### You want to improve quality through multi-agent diversity

Multiple perspectives, adversarial review, or ensemble voting to increase output reliability.

| Pattern | SE Parallel | Module |
|---------|-------------|--------|
| Ensemble / Voting Agent | Quorum reads / consensus | 10 |
| Opponent Processor / Multi-Agent Debate | Chaos engineering, red teams | 10 |
| Recursive Best-of-N Delegation | Tournament selection | 10 |
| Iterative Multi-Agent Brainstorming | RFC process | 10 |
| Explicit Posterior-Sampling Planner | Probabilistic load balancing | 10 |

Debate forces adversarial examination — catches errors a single agent would miss. Ensemble/Voting improves accuracy but multiplies cost linearly.

---

### You need contracts and coordination protocols between agents

Agents must agree on scope, hand off work reliably, or evolve behavior safely.

| Pattern | SE Parallel | Module |
|---------|-------------|--------|
| Feature List as Immutable Contract | Protobuf schemas | 10 |
| Specification-Driven Agent Development | Spec-first API development | 10 |
| Multi-Model Orchestration for Complex Edits | Saga pattern | 10 |
| Parallel Tool Call Learning | Concurrent request optimization | 10 |
| Self-Rewriting Meta-Prompt Loop | JIT compilation | 10 |
| Swarm Migration Pattern | Blue-green deployment | 10 |

Immutable contracts prevent scope creep across agents. Swarm Migration enables safe behavioral updates — old and new agents run in parallel, traffic shifts gradually.

---

### You're building long-running or autonomous agents

Agents that run continuously, process queues, manage their own lifecycle, or operate without constant human oversight.

| Pattern | SE Parallel | Module |
|---------|-------------|--------|
| Continuous Autonomous Task Loop | Event loop / daemon | 11 |
| Autonomous Workflow Agent Architecture | State machines | 11 |
| Custom Sandboxed Background Agent | Isolated workers | 11 |
| Distributed Execution with Cloud Workers | Lambda / serverless | 11 |
| Workspace-Native Multi-Agent Orchestration | K8s pod orchestration | 11 |
| Initializer-Maintainer Dual Agent | Init containers + long-running services | 11 |
| Lane-Based Execution Queueing | Priority queues / swim lanes | 11 |
| Progressive Autonomy with Model Evolution | Feature flags | 11 |
| Stop Hook Auto-Continue Pattern | Pagination cursors | 11 |
| Three-Stage Perception Architecture | ETL pipelines | 11 |
| Tool Capability Compartmentalization | Bounded contexts / DDD | 11 |
| Extended Coherence Work Sessions | Long-running transactions | 16 |

State machines constrain autonomous behavior to valid transitions. Progressive Autonomy gates independence behind demonstrated capability. Extended Coherence prevents drift in long sessions.

---

### Your agent's output is unreliable or needs validation

You need to enforce output schemas, catch errors, test agent behavior, or prevent reward hacking.

| Pattern | SE Parallel | Module |
|---------|-------------|--------|
| Structured Output Specification | JSON Schema / protobuf | 14 |
| Schema Validation Retry with Cross-Step Learning | Retry + circuit breaker | 14 |
| Workflow Evals with Mocked Tools | Integration tests with mocks | 14 |
| CriticGPT-Style Code Review | Automated review bots | 14 |
| Anti-Reward-Hacking Grader Design | Fuzzing / property-based testing | 14 |
| Reliability Problem Map Checklist | Runbooks | 14 |

Structured Output is first line of defense — enforce schemas, eliminate parsing errors. Anti-Reward-Hacking evaluates properties of output, not specific outputs (prevents Goodhart's Law).

---

### Your agent needs within-session self-improvement

The agent should review its own work, use test/CI results as feedback, or improve based on external signals during execution.

| Pattern | SE Parallel | Module |
|---------|-------------|--------|
| Reflection Loop | TDD red-green-refactor | 12 |
| Self-Critique Evaluator Loop | Code review / static analysis | 12 |
| Evaluator-Optimizer | TDD with optimization | 12 |
| Coding Agent CI Feedback Loop | CI/CD pipelines | 12 |
| Background Agent with CI Feedback | Async workers + webhooks | 12 |
| Spec-As-Test Feedback Loop | Contract testing / BDD | 12 |
| Rich Feedback Loops > Perfect Prompts | Observability-driven development | 12 |

Invest in Rich Feedback Loops — an informative environment (good tests, clear errors, CI results) improves agent performance more than perfecting prompts.

---

### You want to learn from production signals across sessions

Turn incidents, reviews, and usage data into systematic improvement of agent behavior.

| Pattern | SE Parallel | Module |
|---------|-------------|--------|
| Incident-to-Eval Synthesis | Post-mortems → regression tests | 12 |
| Inference-Healed Code Review Reward | Reward shaping | 12 |
| Tool Use Incentivization via Reward Shaping | A/B testing | 12 |
| Self-Improving Agent via Feedback Signals | A/B → deploy winner | 13 |
| Iterative Prompt & Skill Refinement | Continuous deployment | 13 |
| Dogfooding with Rapid Iteration | Internal beta programs | 13 |

Incident-to-Eval is the highest-leverage pattern here — every production failure becomes a regression test, compounding quality over time.

---

### You need model-level learning and adaptation

Fine-tuning models on agent trajectories, building reusable skill libraries, or applying RL to agent memory.

| Pattern | SE Parallel | Module |
|---------|-------------|--------|
| Agent Reinforcement Fine-Tuning — Agent RFT | Retraining pipelines | 13 |
| Skill Library Evolution | npm / package registry | 13 |
| Memory Reinforcement Learning — MemRL | Adaptive caching | 13 |
| Variance-Based RL Sample Selection | Stratified sampling | 13 |

Agent RFT is most powerful but risks catastrophic forgetting. Skill Library is safer — turn solved problems into reusable templates without touching weights.

---

### Meta-patterns for building agent products

Strategic patterns that guide how you invest engineering effort, design for model evolution, and ship iteratively.

| Pattern | SE Parallel | Module |
|---------|-------------|--------|
| Compounding Engineering Pattern | Compound interest in tech debt payoff | 13 |
| Frontier-Focused Development | Building for next-gen hardware | 13 |
| Shipping as Research | Lean startup / build-measure-learn | 13 |

Compounding Engineering: invest in eval infrastructure first — it compounds. Frontier-Focused: design for next-gen model capabilities, not just current limitations.

---

### You're deploying agents to production and need operational reliability

Observability, safe rollouts, fallback strategies, governance, and caching for production agent systems.

| Pattern | SE Parallel | Module |
|---------|-------------|--------|
| LLM Observability | OpenTelemetry / Prometheus | 14 |
| Action Caching & Replay | Idempotency keys | 14 |
| Failover-Aware Model Fallback | Failover routing | 14 |
| Canary Rollout and Automatic Rollback | Canary deployments | 14 |
| Versioned Constitution Governance | Policy-as-code / OPA | 14 |
| RLAIF | Automated test feedback loops | 14 |

LLM Observability is non-negotiable — track tokens, latency, errors, cost per request. Canary Rollout applies to prompt changes, model swaps, and tool updates, not just code.

---

### You need to scale agent infrastructure

Handling unbounded work, scaling execution horizontally, building async pipelines, and choosing model architecture.

| Pattern | SE Parallel | Module |
|---------|-------------|--------|
| No-Token-Limit Magic | Pagination + streaming | 16 |
| Adaptive Sandbox Fan-Out Controller | Auto-scaling pools | 16 |
| Asynchronous Coding Agent Pipeline | Async processing pipelines | 16 |
| Merged Code + Language Skill Model | Full-stack vs specialist | 16 |

No-Token-Limit composes auto-compaction + continuation + progressive disclosure + sub-agents to handle work exceeding any single context window.

---

### You need to secure your agent system

Preventing prompt injection, data exfiltration, unauthorized actions, credential exposure, and runaway spending.

| Pattern | SE Parallel | Module |
|---------|-------------|--------|
| Lethal Trifecta Threat Model | STRIDE | 15 |
| Sandboxed Tool Authorization | OAuth scopes / least privilege | 15 |
| Hook-Based Safety Guard Rails | Middleware / interceptors | 15 |
| Egress Lockdown | Network policies / firewall rules | 15 |
| Isolated VM per RL Rollout | gVisor / Firecracker | 15 |
| Zero-Trust Agent Mesh | Service mesh + mTLS | 15 |
| PII Tokenization | PCI-DSS tokenization | 15 |
| External Credential Sync | HashiCorp Vault | 15 |
| Deterministic Security Scanning Build Loop | SAST/DAST | 15 |
| Non-Custodial Spending Controls | Cloud billing hard limits | 15 |
| Soulbound Identity Verification | Certificate pinning | 15 |

The Lethal Trifecta is the organizing framework: actions + data access + autonomy — never allow all three to be high simultaneously. All security controls are infrastructure-enforced, never prompt-enforced.

---

### You're building an agent platform for other developers

Runtime architecture, extension points, developer experience, multi-tenancy, and eval infrastructure at scale.

| Pattern | SE Parallel | Module |
|---------|-------------|--------|
| Virtual Machine Operator Agent | Ansible / Terraform | 17 |
| Subagent Compilation Checker | Build verification | 17 |
| Multi-Platform Communication Aggregation | Unified message bus | 18 |
| Multi-Platform Webhook Triggers | Event-driven architecture | 18 |
| AI Web Search Agent Loop | Web crawler architecture | 19 |

Platform = runtime + platform services (multi-tenancy, billing, event bus) + extension points (tools, hooks, skills) + developer experience (SDK, docs, local dev).

---

### You need to design how humans interact with agents

Trust calibration, approval workflows, transparency, interruption, and handoff between autonomous and supervised modes.

| Pattern | SE Parallel | Module |
|---------|-------------|--------|
| Human-in-the-Loop Approval Framework | PR review / approval gates | 20 |
| Spectrum of Control / Blended Initiative | Self-driving L0-L5 | 20 |
| Seamless Background-to-Foreground Handoff | Async job → notification → UI | 20 |
| Verbose Reasoning Transparency | --verbose / debug mode | 20 |
| Chain-of-Thought Monitoring & Interruption | Kill signals / ctrl+C | 20 |
| Agent-Assisted Scaffolding | create-react-app / cookiecutter | 20 |
| Proactive Trigger Vocabulary | Webhooks / cron expressions | 20 |
| Abstracted Code Representation for Review | Diff views | 20 |

Trust is the core challenge. Risk-tier your approvals: auto-approve low-risk, notify medium, require approval for high-risk, block catastrophic. Spectrum of Control is adjustable per task and per action type.

---

### You need to adopt agents across a team or organization

Shared configuration, workflow design for agent compatibility, codebase optimization, organizational change.

| Pattern | SE Parallel | Module |
|---------|-------------|--------|
| Team-Shared Agent Configuration as Code | .editorconfig / infra-as-code | 21 |
| Agent-Friendly Workflow Design | Idempotent APIs | 21 |
| AI-Accelerated Learning and Skill Development | Pair programming | 21 |
| Codebase Optimization for Agents | Clean architecture | 21 |
| Democratization of Tooling via Agents | No-code platforms | 21 |
| Dev Tooling Assumptions Reset | Paradigm shifts | 21 |
| Latent Demand Product Discovery | Jobs-to-be-done | 21 |
| Milestone Escrow for Agent Resource Funding | Milestone payments | 21 |

Agent-Friendly Workflow Design (structured issues, reliable tests, clear CI output) determines agent effectiveness more than prompt engineering. Codebase Optimization (type hints, READMEs, test coverage) benefits both humans and agents.

---

## Module Details

Each entry describes the mental models the module builds — what you understand after reading it, not just what topics it covers.

---

### Module 1: What LLMs Actually Are
- **Path**: `part-1-foundations/01-what-llms-are.md`
- **SE Parallel**: A database engine — storage format (weights), query language (prompts), query planner (attention)
- **Builds on**: Nothing. Start here.
- **Summary**: After this module, you understand that an LLM is a stateless function: tokens in, probability distribution out. All state management is your problem. The context window is the model's RAM — fixed size, O(n^2) cost to process. Three types of knowledge exist: parametric (frozen in weights), contextual (in the prompt), and retrieved (fetched by tools at runtime). Temperature controls the determinism/creativity trade-off. Model selection is always a cost/latency/quality triangle.

### Module 2: The Economics of Inference
- **Path**: `part-1-foundations/02-economics-of-inference.md`
- **SE Parallel**: Cloud compute pricing — metered resource where architecture determines cost trajectory
- **Builds on**: Module 1
- **Summary**: After this module, you understand that cost is a first-class architectural constraint, not an afterthought. Inference has two phases: prefill (cheap, parallel, processes input) and decode (expensive, sequential, generates output). Input tokens cost 3-5x less than output tokens — design prompts to be input-heavy. Conversation history re-processes every turn, so cost grows quadratically with conversation length. Prompt caching (exact byte-prefix match) gives ~90% discount — this drives architectural decisions about prompt structure. Extended thinking tokens are output-priced, so use selectively.

### Module 3: From Prompting to Programming
- **Path**: `part-1-foundations/03-prompting-to-programming.md`
- **SE Parallel**: Evolution from shell one-liners to structured programming
- **Builds on**: Modules 1-2
- **Summary**: After this module, you treat prompts as programs deserving version control, testing, and deployment discipline. System prompt is main(), messages are the call stack, parameters are compiler flags. Few-shot examples are the most reliable steering mechanism — they serve as both specification and test cases. Chain-of-thought trades tokens for accuracy. Structured output (JSON Schema / constrained decoding) eliminates parsing errors. The agent is defined: a loop of prompted LLM calls with tool use and state management.

### Module 4: Anatomy of an Agent
- **Path**: `part-2-single-agent/04-anatomy-of-an-agent.md`
- **SE Parallel**: Web application framework — request-response loop, middleware, route handlers, session management
- **Builds on**: Modules 1-3
- **Summary**: After this module, you can decompose any agent into six subsystems: system prompt (bootstrap config), reasoning engine (the LLM), tool registry (available capabilities with schemas), tool executor (dispatch and result formatting), state manager (memory across turns), and stop conditions (budget, turns, errors, time). The critical distinction: an agent is a system where the LLM makes control-flow decisions. A workflow has predetermined steps. This distinction drives every architectural choice in the rest of the course.

### Module 5: Reasoning Patterns
- **Path**: `part-2-single-agent/05-reasoning-patterns.md`
- **SE Parallel**: Algorithm design strategies — greedy, divide-and-conquer, dynamic programming, backtracking
- **Builds on**: Module 4
- **Patterns**: Chain-of-Thought, ReAct, Plan-Then-Execute, Tree-of-Thought, Graph of Thoughts, Self-Discover, LATS, Inference-Time Scaling
- **Summary**: After this module, you understand reasoning as a compute/quality trade-off with a spectrum of strategies. ReAct (alternate thinking and acting) is the default — it maps to the OODA loop. Plan-Then-Execute separates strategy from tactics, enabling a cheap model for execution. Tree-of-Thought explores multiple paths (branch-and-bound), costing 10-100x more. Inference-Time Scaling is the meta-pattern: route easy tasks to cheap inference, hard tasks to extended thinking or tree search — the agent equivalent of autoscaling.

### Module 6: Tool Use Patterns
- **Path**: `part-2-single-agent/06-tool-use-patterns.md`
- **SE Parallel**: API design and integration patterns
- **Builds on**: Modules 4-5
- **Patterns**: LLM-Friendly API Design, Dual-Use Tool Design, Shell Command Contextualization, Progressive Tool Discovery, Code Mode MCP Tool Interface, Agent SDK for Programmatic Control, CodeAct Agent, Dynamic Code Injection, Code-Over-API, Intelligent Bash Tool Execution, Action-Selector, Tool Use Steering via Prompting, Patch Steering via Prompted Tool Selection, Agentic Search Over Vector Embeddings, Visual AI Multimodal Integration, Conditional Parallel Tool Execution, CLI-Native Agent Orchestration, CLI-First Skill Design, Code-Then-Execute
- **Summary**: After this module, you understand that tool design determines agent effectiveness — it's the equivalent of API design for developers. Tools need descriptions that say *when* to use them, not just what they do. Three progressions are covered: how agents find tools (progressive discovery — don't dump all tools upfront), how agents choose between tools (action-selector, steering via prompting), and how agents execute tools safely (CodeAct for flexibility with sandboxing, constrained tool calls for production safety). MCP is the interoperability standard — gRPC/protobuf for the agent ecosystem.

### Module 7: Memory, Context & State
- **Path**: `part-2-single-agent/07-memory-context-state.md`
- **SE Parallel**: Storage hierarchy — CPU registers through cold storage
- **Builds on**: Modules 4-6
- **Patterns**: Context Window Auto-Compaction, Context-Minimization, Curated Code/File Context Window, Progressive Disclosure for Large Files, Semantic Context Filtering, Prompt Caching via Exact Prefix Preservation, Dynamic Context Injection, Layered Configuration Context, Hierarchical Memory, Working Memory via TodoWrite, RAG, Episodic Memory Retrieval & Injection, Memory Synthesis from Execution Logs, Self-Identity Accumulation, Agent-Powered Codebase Q&A, Filesystem-Based Agent State, Proactive Agent State Externalization
- **Summary**: After this module, you understand context management as the agent equivalent of memory hierarchy design. The context window is L1 cache — fast, small, expensive. Three-tier memory: working (context window), main (session-scoped, compacted out but retrievable), archive (persistent, filesystem/database). Context-Minimization is highest-impact: every token costs O(n^2) in attention. Prompt Caching via exact prefix preservation is the biggest cost lever (70% hit rate saves 63% input cost — this is CDN caching for LLMs). RAG bridges the knowledge cutoff by retrieving fresh information at runtime. State externalization (filesystem, checkpoints) enables long-running agents to survive context resets.

### Module 8: Why Multi-Agent
- **Path**: `part-3-multi-agent/08-why-multi-agent.md`
- **SE Parallel**: Monolith-to-microservices transition
- **Builds on**: Modules 4-7
- **Patterns**: Router Agent / Model Selection, Dual LLM Pattern, Budget-Aware Model Routing with Hard Cost Caps, Progressive Complexity Escalation, Agent Modes by Model Personality
- **Summary**: After this module, you understand when and why to split a monolith agent into multiple agents. The same forces that drive microservices apply: context limits (one agent can't hold everything), capability mismatch (expensive model wasted on simple tasks), latency requirements (fast path vs. deep reasoning), and reliability (blast radius isolation). Router Agent is foundational — classify task, route to cheapest capable model. Dual LLM (frontier planner + cheap executor) saves 60-80%. Budget-Aware Routing with hard cost caps prevents runaway spending at the infrastructure level.

### Module 9: Orchestration Architectures
- **Path**: `part-3-multi-agent/09-orchestration-architectures.md`
- **SE Parallel**: Distributed system topologies — master-worker, peer-to-peer, pub-sub
- **Builds on**: Module 8
- **Patterns**: Orchestrator-Worker, Planner-Worker Separation, Sub-Agent Spawning, Oracle and Worker Multi-Model Approach, LLM Map-Reduce, Factory over Assistant, Inversion of Control, Hybrid LLM/Code Workflow Coordinator, Discrete Phase Separation
- **Summary**: After this module, you can select the right multi-agent topology for a given problem. Orchestrator-Worker is the default (master-worker). Sub-Agent Spawning solves context exhaustion by giving each subtask a fresh context window (fork/exec). LLM Map-Reduce processes inputs exceeding any single context window: parallel cheap-model phase, then frontier model reduces. Factory over Assistant creates purpose-built, isolated agents per task type (no shared state contamination). The key insight: Hybrid LLM/Code is most cost-effective — use deterministic code for predictable steps, reserve LLM agents only for steps requiring reasoning.

### Module 10: Communication & Coordination
- **Path**: `part-3-multi-agent/10-communication-coordination.md`
- **SE Parallel**: Distributed consensus and collaboration protocols
- **Builds on**: Modules 8-9
- **Patterns**: Ensemble / Voting Agent, Opponent Processor / Multi-Agent Debate, Recursive Best-of-N Delegation, Iterative Multi-Agent Brainstorming, Explicit Posterior-Sampling Planner, Feature List as Immutable Contract, Specification-Driven Agent Development, Multi-Model Orchestration for Complex Edits, Parallel Tool Call Learning, Self-Rewriting Meta-Prompt Loop, Swarm Migration Pattern
- **Summary**: After this module, you understand how multiple agents improve quality through diversity and how to maintain coherence across agents. Ensemble/Voting is quorum reads — majority agreement increases reliability. Debate forces adversarial examination, catching errors a single agent misses. Feature List as Immutable Contract is the protobuf schema for agent coordination — prevents scope creep. Multi-Model Orchestration applies the saga pattern to multi-file edits (plan → execute per file → verify → compensate on failure). Swarm Migration enables safe behavioral evolution — old and new agent populations run simultaneously, traffic shifts gradually.

### Module 11: Advanced Orchestration
- **Path**: `part-3-multi-agent/11-advanced-orchestration.md`
- **SE Parallel**: Production infrastructure — long-running daemons, container orchestration, priority queues
- **Builds on**: Modules 8-10
- **Patterns**: Continuous Autonomous Task Loop, Autonomous Workflow Agent Architecture, Custom Sandboxed Background Agent, Distributed Execution with Cloud Workers, Workspace-Native Multi-Agent Orchestration, Initializer-Maintainer Dual Agent, Lane-Based Execution Queueing, Progressive Autonomy with Model Evolution, Three-Stage Perception Architecture, Tool Capability Compartmentalization, Stop Hook Auto-Continue Pattern
- **Summary**: After this module, you can design agents that run autonomously for extended periods. Continuous Task Loop turns agents into daemons processing work queues. State machines constrain autonomous behavior to valid transitions — the agent can only do what the state machine allows. Initializer-Maintainer separates expensive setup (load context, build understanding) from cheap ongoing execution. Progressive Autonomy gates agent independence behind demonstrated capability (feature flags for trust). Stop Hook Auto-Continue serializes state and continues across context boundaries — pagination for agent execution.

### Module 12: Feedback Loops
- **Path**: `part-4-feedback-learning/12-feedback-loops.md`
- **SE Parallel**: CI/CD and observability — mechanisms that tell you if the system works correctly
- **Builds on**: Modules 4-11
- **Patterns**: Reflection Loop, Self-Critique Evaluator Loop, Evaluator-Optimizer, Coding Agent CI Feedback Loop, Background Agent with CI Feedback, Spec-As-Test Feedback Loop, Rich Feedback Loops > Perfect Prompts, Incident-to-Eval Synthesis, Inference-Healed Code Review Reward, Tool Use Incentivization via Reward Shaping
- **Summary**: After this module, you understand feedback as the primary mechanism for agent quality — more important than prompt engineering. Three feedback scopes: within-session (reflection, self-critique — the agent reviews its own work), external (CI results, test failures — unambiguous signals), and systemic (incident-to-eval, reward shaping — learning across sessions). The key insight: Rich Feedback Loops > Perfect Prompts. An informative environment (good tests, clear error messages, CI results) improves agent performance more than perfecting prompts. Incident-to-Eval Synthesis compounds — every production failure becomes a regression test.

### Module 13: Learning & Adaptation
- **Path**: `part-4-feedback-learning/13-learning-adaptation.md`
- **SE Parallel**: Continuous delivery and platform evolution
- **Builds on**: Module 12
- **Patterns**: Self-Improving Agent via Feedback Signals, Iterative Prompt & Skill Refinement, Dogfooding with Rapid Iteration, Agent RFT, Skill Library Evolution, MemRL, Variance-Based RL Sample Selection, Compounding Engineering Pattern, Frontier-Focused Development, Shipping as Research
- **Summary**: After this module, you understand three levels of agent learning. Prompt-level: automated feedback signals adjust prompts (Self-Improving Agent). Capability-level: solved problems become reusable templates (Skill Library Evolution — the npm for agent capabilities). Model-level: fine-tune on successful trajectories (Agent RFT — most powerful, but risks catastrophic forgetting). Three meta-patterns guide strategy: Compounding Engineering (invest in eval infrastructure first — it compounds), Frontier-Focused Development (design for next-gen model capabilities, not current limitations), Shipping as Research (production is the best lab).

### Module 14: Reliability Engineering
- **Path**: `part-5-production-hardening/14-reliability-engineering.md`
- **SE Parallel**: SRE — monitoring, testing, rollout procedures, incident response
- **Builds on**: Modules 4-13
- **Patterns**: Structured Output Specification, Schema Validation Retry with Cross-Step Learning, Workflow Evals with Mocked Tools, CriticGPT-Style Code Review, Action Caching & Replay, Failover-Aware Model Fallback, LLM Observability, RLAIF, Canary Rollout and Automatic Rollback, Versioned Constitution Governance, Anti-Reward-Hacking Grader Design, Reliability Problem Map Checklist
- **Summary**: After this module, you understand that agent failures are stochastic — you need traditional SRE practices plus infrastructure for nondeterminism. Structured Output is first defense (enforce schemas at the model output layer). LLM Observability is non-negotiable (track tokens, latency, errors, cost — per request). Canary Rollout applies to all agent changes: prompt updates, model swaps, tool modifications. Versioned Constitution provides auditable governance (policy-as-code for agent behavior). Anti-Reward-Hacking: evaluate properties of output, not specific outputs — prevents Goodhart's Law from corrupting your evals.

### Module 15: Security & Safety
- **Path**: `part-5-production-hardening/15-security-safety.md`
- **SE Parallel**: Defense in depth — firewalls, auth, encryption, auditing, sandboxing
- **Builds on**: Module 14
- **Patterns**: Lethal Trifecta Threat Model, Sandboxed Tool Authorization, Hook-Based Safety Guard Rails, Egress Lockdown, Isolated VM per RL Rollout, Zero-Trust Agent Mesh, PII Tokenization, External Credential Sync, Deterministic Security Scanning Build Loop, Non-Custodial Spending Controls, Soulbound Identity Verification
- **Summary**: After this module, you understand that the LLM is an untrusted component — all security controls operate around it, never through it. The Lethal Trifecta is the organizing framework: real-world actions + sensitive data access + unsupervised autonomy — never allow all three to be high simultaneously. Credentials and PII must never enter the context window (use tokenization and external vaults). Egress Lockdown prevents data exfiltration regardless of what the agent tries. All spending controls are infrastructure-enforced (hard caps in billing systems), never prompt-enforced. Prompt injection is the primary novel attack surface — defense is layered, not a single filter.

### Module 16: Cost, Scaling & Operations
- **Path**: `part-5-production-hardening/16-cost-scaling-operations.md`
- **SE Parallel**: Capacity planning and infrastructure operations
- **Builds on**: Modules 14-15
- **Patterns**: No-Token-Limit Magic, Adaptive Sandbox Fan-Out Controller, Asynchronous Coding Agent Pipeline, Extended Coherence Work Sessions, Merged Code + Language Skill Model
- **Summary**: After this module, you can design agent systems that handle unbounded work and scale horizontally. No-Token-Limit Magic composes auto-compaction + continuation + progressive disclosure + sub-agents to handle work exceeding any single context window. Adaptive Sandbox Fan-Out scales execution environments horizontally based on demand. Extended Coherence prevents drift in long sessions through periodic self-consistency checks. The operational disciplines covered: cost attribution per tenant/task, capacity planning for bursty inference workloads, and graceful degradation when models or providers fail.

### Module 17: Agent Runtime Architecture
- **Path**: `part-6-agent-platform/17-agent-runtime-architecture.md`
- **SE Parallel**: Application server internals — request lifecycle, process isolation, plugin architecture
- **Builds on**: Modules 4-16
- **Patterns**: Virtual Machine Operator Agent, Subagent Compilation Checker
- **Summary**: After this module, you can design the internals of an agent runtime (the equivalent of building Tomcat, not deploying to it). Five layers: Session Manager (lifecycle, authentication, persistence), Prompt Compositor (layered assembly with cache-optimal ordering — static content first for prefix caching), Tool Execution Engine (middleware pipeline: parse → validate → authorize → execute → format → inject), Sandbox Orchestrator (isolation, filesystem sync, resource limits), Model Abstraction Layer (provider switching, fallback, load balancing). The architecture is reverse-engineered from Claude Code, Cursor, and Devin.

### Module 18: Building Developer Platforms
- **Path**: `part-6-agent-platform/18-building-developer-platforms.md`
- **SE Parallel**: Platform engineering — tools, SDKs, APIs, extension points
- **Builds on**: Module 17
- **Patterns**: Multi-Platform Communication Aggregation, Multi-Platform Webhook Triggers
- **Summary**: After this module, you understand the four-layer platform stack: runtime (Module 17), platform services (multi-tenancy, event bus, billing, audit), extension points (tool registry/packaging, hooks, skills, custom models), and developer experience (SDK with progressive complexity, local development environment, documentation, templates). Tool ecosystem design (registry, packaging, discovery) determines platform value — it's the npm/pip moment. Webhook Triggers enable event-driven automation (GitHub push → agent session). Communication Aggregation unifies outbound messaging across platforms.

### Module 19: Eval Infrastructure at Scale
- **Path**: `part-6-agent-platform/19-eval-infrastructure-at-scale.md`
- **SE Parallel**: CI/CD infrastructure — not the tests, but the systems that run them at scale
- **Builds on**: Modules 12, 17-18
- **Patterns**: AI Web Search Agent Loop
- **Summary**: After this module, you understand eval infrastructure as the most important investment for an agent platform — it compounds over time and becomes a moat. Four-stage pipeline: Case Management (design, version, stratified sampling), Execution (parallel, deterministic seeding, resource-isolated), Grading (layered: exact-match → rule-based → LLM-as-judge → human calibration), Reporting & Gating (dashboards, deploy gates that block regressions). The eval flywheel: evals catch issues → incidents generate new eval cases → grading calibrates against human judgment → quality compounds.

### Module 20: Interaction Patterns
- **Path**: `part-7-ux-collaboration/20-interaction-patterns.md`
- **SE Parallel**: UI design for complex systems — progressive disclosure, approval workflows, real-time feedback
- **Builds on**: Modules 4-19
- **Patterns**: Human-in-the-Loop Approval Framework, Spectrum of Control / Blended Initiative, Seamless Background-to-Foreground Handoff, Verbose Reasoning Transparency, Chain-of-Thought Monitoring & Interruption, Agent-Assisted Scaffolding, Proactive Trigger Vocabulary, Abstracted Code Representation for Review
- **Summary**: After this module, you understand trust as the core UX challenge for agent systems. Risk-tiered approvals prevent approval fatigue: auto-approve safe actions, notify for medium-risk, require explicit approval for high-risk, block catastrophic. Spectrum of Control (L0 manual through L5 fully autonomous) is adjustable per task type and per action within a task. Background-to-Foreground Handoff enables autonomous work with seamless human re-engagement when needed. Abstracted Code Representation (diffs, summaries, impact analysis) makes agent output reviewable without reading every line.

### Module 21: Team & Organizational Patterns
- **Path**: `part-7-ux-collaboration/21-team-organizational-patterns.md`
- **SE Parallel**: DevOps culture and organizational design
- **Builds on**: Module 20
- **Patterns**: Team-Shared Agent Configuration as Code, Agent-Friendly Workflow Design, AI-Accelerated Learning and Skill Development, Codebase Optimization for Agents, Democratization of Tooling via Agents, Dev Tooling Assumptions Reset, Latent Demand Product Discovery, Milestone Escrow for Agent Resource Funding
- **Summary**: After this module, you understand agents as team infrastructure, not individual productivity tools. Configuration as Code ensures consistency across team members. Agent-Friendly Workflow Design (structured issues, reliable tests, clear CI output) determines agent effectiveness more than any prompt technique. Codebase Optimization (type annotations, modular architecture, comprehensive tests) benefits both human and agent developers. Milestone Escrow ties agent compute cost to verified value delivery — the business model for autonomous agent work.

### Module 22: End-to-End Platform Design
- **Path**: `part-8-capstone/22-end-to-end-platform-design.md`
- **SE Parallel**: System design interview whiteboard
- **Builds on**: All prior modules
- **Summary**: A complete design of a "Codex" platform for a 200-person engineering organization. Integrates patterns from every prior module into a coherent architecture: hybrid inference (API + self-hosted for cost/privacy), container sandboxes per session, 3-model tier with routing (fast/balanced/frontier), eval pipeline as deploy gate, multi-tier memory, WebSocket sessions with reconnection, cost attribution per team, security defense-in-depth. Every design decision maps to a named pattern from the course.

### Module 23: The Evolving Landscape
- **Path**: `part-8-capstone/23-evolving-landscape.md`
- **SE Parallel**: Technology forecasting through architectural principles
- **Builds on**: All prior modules
- **Summary**: Distinguishes durable patterns (rooted in fundamental constraints — state management, economics, security, evals, human-agent trust) from transitional patterns (addressing current model limitations — complex reasoning chains, aggressive context minimization). Durable patterns deserve heavy investment; transitional patterns need swappable implementations. Emerging frontiers: agent-to-agent economies, continuous learning without catastrophic forgetting, multi-modal native workflows, formal verification of agent behavior. The course's final principle: always build the feedback loop first.

---

## Glossary — Course-Specific Terms

Terms below have definitions specific to this course that differ from or are more precise than common usage. Standard LLM/ML terminology (token, temperature, transformer, fine-tuning, etc.) is used with conventional meanings throughout.

| Term | Definition (as used in this course) | SE Parallel |
|------|--------------------------------------|-------------|
| **Agent** | A system where the LLM makes control-flow decisions — choosing tools, whether to continue, what to investigate. Explicitly distinguished from **workflows** (predetermined steps) and **pipelines** (fixed sequences). This distinction drives all architectural choices in the course. | Web app with dynamic routing |
| **Agent loop** | The six-step execution cycle: compose context → call LLM → parse response → execute tool or return → check stop conditions → repeat. The atomic unit of agent execution. | Request-response loop |
| **Agent runtime** | The execution environment managing an agent's full lifecycle. Five layers in this course's model: Session Manager, Prompt Compositor, Tool Execution Engine, Sandbox Orchestrator, Model Abstraction Layer. | Application server (Tomcat, Express) |
| **Auto-compaction** | Lossy compression of older conversation history when context approaches its limit. The course treats this as LRU eviction — necessary, dangerous, and requiring careful summary strategy. | Buffer pool eviction / LRU cache |
| **Constitution (agent)** | A versioned, auditable rule set governing agent behavior. Infrastructure-enforced (injected into system prompt + validated by runtime), never advisory. | Policy-as-code / OPA |
| **Deploy gate** | Automated quality check that blocks agent changes (prompts, models, tools) if eval metrics regress. The agent equivalent of CI blocking a merge. | CI/CD quality gate |
| **Eval pipeline** | Four-stage infrastructure: case management → parallel execution → layered grading (exact-match → rule → LLM-judge → human) → reporting with deploy gates. The course's position: this is the most important investment for agent platforms. | CI/CD infrastructure |
| **Hierarchical Memory** | Three-tier model used throughout: **working** (context window — L1, fast, small), **main** (session-scoped, compacted out — L2/L3), **archive** (persistent across sessions — disk/database). | CPU cache hierarchy L1/L2/L3 |
| **Lethal Trifecta** | The course's organizing security framework: real-world actions + sensitive data access + unsupervised autonomy. The rule: never allow all three to be high simultaneously. | STRIDE threat model |
| **MCP (Model Context Protocol)** | Standard protocol connecting agents to external tool servers via typed interfaces. The course positions this as the interoperability layer for the agent ecosystem. | gRPC + protobuf |
| **Prompt caching** | Provider optimization reusing KV cache when request byte-prefix matches. ~90% discount. The course emphasizes this drives prompt *architecture* — static content must come first. | CDN edge caching |
| **Prompt injection** | Malicious content in input/retrieved documents that hijacks agent behavior. The course treats this as the primary novel attack surface for agents — defense is layered, never a single filter. | SQL injection / XSS |
| **Skill library** | Growing collection of reusable agent capabilities (prompt templates, tool chains, workflows) extracted from successful completions. The course's evolutionary path for agent capability. | Package registry (npm/pip) |
| **Spectrum of Control** | The course's autonomy continuum: L0 (manual) → L1 (suggest) → L2 (confirm) → L3 (autonomous + review) → L4 (autonomous + audit) → L5 (fully autonomous). Adjustable per task type and per action within a task. | Self-driving levels L0-L5 |
| **Stop condition** | Rule terminating the agent loop. The course's position: these are mandatory and must include budget, turn limit, error threshold, and time limit — not optional. | Circuit breaker / timeout |
