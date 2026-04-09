# Module 9: Orchestration Architectures

**Software engineering parallel**: Distributed system topologies — master-worker, peer-to-peer, pub-sub, choreography vs. orchestration. Each topology has different failure modes, scaling properties, and coordination overhead.

**Patterns covered**: Orchestrator-Worker, Planner-Worker Separation, Sub-Agent Spawning, Oracle and Worker Multi-Model Approach, LLM Map-Reduce Pattern, Factory over Assistant, Inversion of Control, Hybrid LLM/Code Workflow Coordinator, Discrete Phase Separation

---

## The Topology Question

Module 8 established *why* you need multiple agents. This module addresses *how* to organize them. The central question is: who decides what work gets done, and who does it?

Every multi-agent architecture is a variant of one fundamental choice: **centralized orchestration** (one agent directs others) vs. **decentralized coordination** (agents negotiate among themselves). Most production systems use centralized orchestration — it's simpler to debug, reason about, and control.

## Pattern: Orchestrator-Worker

**What it does**: A single orchestrator agent receives the task, decomposes it into subtasks, assigns each to a worker agent, collects results, and synthesizes the final output.

**SE parallel**: Master-worker in distributed computing (Spark driver + executors, Kubernetes controller + pods). The master holds the global state and makes scheduling decisions; workers execute assigned work and report results.

**How it works**:
```
Orchestrator (frontier model):
  1. Receive: "Add OAuth2 support to the auth module"
  2. Decompose: [research OAuth2 flow, modify auth handler,
                 add token storage, update tests, update docs]
  3. Assign: worker_1 → research, worker_2 → modify handler, ...
  4. Collect results, check coherence
  5. Synthesize final response

Workers (mid-tier models):
  Each receives: specific subtask + relevant context only
  Each returns: completed work + status
```

**When to use it**: Tasks that decompose into largely independent subtasks. The orchestrator handles the coordination overhead; workers handle the execution.

**Trade-off**: The orchestrator is a single point of failure. If it misdecomposes the task, all workers do the wrong work. The orchestrator also becomes a bottleneck — every result flows through it. For deeply sequential tasks where each step depends on the previous, this pattern adds overhead without benefit.

## Pattern: Planner-Worker Separation

**What it does**: A strict variant of Orchestrator-Worker where the planner *only* plans and the workers *only* execute. The planner has no tools; workers have no planning capability.

**SE parallel**: Control plane vs. data plane. In networking, the control plane decides *where* packets go; the data plane *moves* them. They're separate systems with different scaling, reliability, and security requirements. Planner-Worker applies the same separation.

**Why separate them?** The planner needs a frontier model, broad context, and creative reasoning. Workers need cheaper models, narrow context, and precise execution. Combining both into every agent wastes compute — the worker doesn't need the planner's expensive reasoning capability, and the planner doesn't need the worker's tools.

**Trade-off**: Same as Plan-Then-Execute (Module 5) — the plan can be wrong. The mitigation is a feedback loop: workers report results back to the planner, which adjusts the plan. This makes it a hybrid of orchestration and ReAct at the system level.

## Pattern: Sub-Agent Spawning

**What it does**: An agent dynamically creates child agents to handle subtasks, each with their own context window, tool set, and system prompt. The parent agent decides when to spawn, what context to provide, and how to integrate results.

**SE parallel**: fork/exec in Unix, or thread pools. The parent process spawns child processes for parallel work. Each child has its own memory space (context window), runs independently, and returns a result to the parent.

**Why it's powerful**: Each sub-agent gets a fresh context window. If the parent's context is full, spawning a sub-agent with only the relevant context solves the context exhaustion problem. The sub-agent can perform deep research without polluting the parent's context with irrelevant details.

**Scenario**: A coding agent needs to understand how the authentication system works before modifying it. Instead of reading 20 files itself (consuming context), it spawns a sub-agent: "Research the authentication system in this codebase. Return: the auth flow, key files, and how sessions are managed." The sub-agent reads the files in its own context, synthesizes the answer, and returns a compact summary. The parent gets the knowledge without the context cost.

**Trade-off**: Spawned agents lose the parent's full context. If the subtask needs information from the parent's earlier conversation, you must explicitly pass it. Under-providing context produces shallow results; over-providing negates the context savings.

## Pattern: Oracle and Worker Multi-Model Approach

**What it does**: A powerful "oracle" model makes decisions and evaluates quality, while cheaper "worker" models do the bulk execution. The oracle sees everything but does little; workers do everything but see little.

**SE parallel**: Coordinator-worker pattern in distributed databases (e.g., Raft leader). The leader (oracle) maintains authority and consistency; followers (workers) handle read requests. The leader intervenes only when consistency requires it.

**How it differs from Dual LLM (Module 8)**: The Dual LLM pattern uses two models in a fixed pipeline (plan → execute). Oracle-Worker is more dynamic — the oracle reviews worker output, provides corrections, and may redirect work. It's a supervisory relationship, not a pipeline.

**When to use it**: Complex tasks where quality assurance is critical. The oracle reviews every worker output before it's committed, catching errors that a cheaper model produces. Costs more than pure worker execution but much less than using the oracle for everything.

### Real-World Example: Anthropic's Advisor Strategy

In April 2026, Anthropic shipped the **Advisor Strategy** as a first-party platform feature on the Claude API. It's a production implementation of Oracle-Worker with a critical architectural twist: **the cheap model delegates up, not the expensive model delegating down**.

**Architecture**:
```
┌─────────────────────────────────────────────────────┐
│                  Main Loop                          │
│                                                     │
│  ┌───────────────┐        ┌──────────────────────┐  │
│  │   Executor    │──tool──▶│      Advisor        │  │
│  │   (Sonnet)    │  call  │      (Opus)          │  │
│  │ Runs every    │◀───────│   On-demand only     │  │
│  │   turn        │ advice │                      │  │
│  └───────┬───────┘        └──────────┬───────────┘  │
│          │                           │              │
│          │ read/write        reviews │              │
│          ▼                           ▼              │
│  ┌─────────────────────────────────────────────┐    │
│  │         Shared Context                      │    │
│  │   (conversation + tools + history)          │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

**Why this matters architecturally**: In the Dual LLM Pattern (Module 8), the expensive model sits at the top — it plans, and the cheap model executes. The Advisor Strategy inverts this. The cheap model (Sonnet) runs the main agent loop, handles routine tool calls, and manages the conversation. When it encounters a decision that exceeds its capability — an architectural question, a subtle bug, a trade-off evaluation — it invokes the expensive model (Opus) *as a tool call*. The advisor reviews the shared context, provides guidance, and returns control to the executor.

**SE parallel**: This is an escalation callback, not a coordinator-worker. Think of it as a junior developer who handles the sprint backlog independently but pings the staff engineer for design reviews — not a tech lead who assigns all tasks. The staff engineer doesn't manage the workflow; they're consulted on-demand.

**Shared context, not passed context**: A key design choice is that the advisor reads the *same* shared context (full conversation, tool history, file state) rather than receiving a summarized handoff from the executor. This avoids the lossy compression problem that plagues planner-worker architectures where the planner must distill complex state into instructions. It's the difference between shared memory (the advisor reads the executor's heap directly) and message passing (the executor serializes state into a message).

**Results**: Sonnet with an Opus advisor scored 74.8% on SWE-bench Multilingual — up 2.7 points from Sonnet alone (72.1%) — while cutting costs 11.9% per task. Haiku as executor with Opus as advisor showed even larger relative gains. The cost savings come from the advisor being invoked only on hard decisions rather than running every turn.

**Takeaway for system design**: The Advisor Strategy validates a general principle — the right default for multi-model architectures is often "cheap model drives, expensive model advises" rather than "expensive model plans, cheap model executes." The cheap model handles the 80% it's competent at without round-tripping to the expensive model, and the expensive model's context window isn't consumed by routine operations.

## Pattern: LLM Map-Reduce

**What it does**: Applies the MapReduce paradigm to LLM processing — split a large input into chunks, process each chunk independently (map), then combine results (reduce).

**SE parallel**: MapReduce / Spark. The canonical distributed data processing pattern: partition the data, process partitions in parallel, aggregate results. LLM Map-Reduce applies this to tasks that operate on large corpora.

**How it works**:
```
Input: 500-page codebase documentation

Map phase (parallel, cheap model):
  Chunk 1 (pages 1-25)   → "summarize security-relevant sections"
  Chunk 2 (pages 26-50)  → "summarize security-relevant sections"
  ...
  Chunk 20 (pages 476-500) → "summarize security-relevant sections"

Reduce phase (frontier model):
  All 20 summaries → "synthesize into a complete security audit"
```

**When to use it**: Any task that needs to process more content than fits in a single context window — document analysis, codebase auditing, large-scale refactoring analysis. The map phase is embarrassingly parallel and can use cheap models; the reduce phase needs a capable model to synthesize.

**Trade-off**: Information loss at chunk boundaries. If a security vulnerability spans pages 24-26, and the boundary falls at page 25, neither chunk has the full picture. Mitigations: overlapping chunks (redundant but safer), multi-pass (map once for structure, then again with structure-aware chunking).

## Pattern: Factory over Assistant

**What it does**: Instead of creating a single long-lived agent that accumulates state, creates fresh, purpose-built agents for each task or task type. Each agent is configured with exactly the right system prompt, tools, and context for its specific job.

**SE parallel**: Factory pattern in OOP. Instead of configuring one God Object, you use a factory that produces specialized instances. `AgentFactory.create("code_reviewer")` produces a different agent than `AgentFactory.create("test_writer")` — different prompts, different tools, different models.

**Why not just switch modes?** Agent Modes (Module 8) switches configuration within a single agent. Factory over Assistant creates entirely new agents with clean context. The difference matters when you need isolation: a code reviewer agent shouldn't be influenced by the previous edit agent's conversation history.

**When to use it**: Platforms that serve multiple task types. Each task gets a purpose-built agent rather than a general-purpose agent trying to be everything. This is how production platforms like Claude Code work — different task types invoke differently-configured agents.

## Pattern: Inversion of Control

**What it does**: Instead of the agent controlling its own execution loop, the execution environment controls the agent — calling it when needed, providing context, and deciding what to do with results.

**SE parallel**: IoC/Dependency Injection / Hollywood Principle ("don't call us, we'll call you"). A Spring-managed bean doesn't control its lifecycle — the container does. Similarly, an IoC agent doesn't decide when to run or what context to receive — the orchestration framework decides.

**How it works**: The agent is a pure function: context in, decision out. The framework handles the loop, state management, tool execution, and result routing. The agent has no awareness of other agents, the broader task, or the orchestration topology.

**Why it matters**: IoC makes agents composable and testable. You can swap one agent implementation for another without changing the orchestration. You can test an agent in isolation by mocking the framework. This is the architectural principle that enables all the other patterns in this module.

## Pattern: Hybrid LLM/Code Workflow Coordinator

**What it does**: Combines deterministic code (traditional workflows) with LLM-powered agents at specific decision points. The workflow handles the predictable parts; agents handle the ambiguous parts.

**SE parallel**: Apache Airflow with smart tasks. Airflow DAGs define the workflow structure in code. Most tasks are deterministic (run ETL, execute SQL). But some tasks need judgment — "determine if this data anomaly is a real issue." Those tasks call an LLM agent. The workflow coordinator manages the overall flow.

**Why it matters**: Module 4 distinguished agents from workflows. The Hybrid pattern combines them: use workflows for the 80% that's predictable, and agents for the 20% that requires reasoning. This is the most cost-effective architecture for most production systems.

**Scenario**: A CI/CD pipeline for agent-generated code:
1. Agent writes code (LLM) → 2. Run tests (deterministic) → 3. If tests fail, agent analyzes failures (LLM) → 4. Agent fixes code (LLM) → 5. Run tests again (deterministic) → 6. If pass, create PR (deterministic)

Steps 2, 5, 6 are code. Steps 1, 3, 4 are agents. The coordinator manages the flow.

## Pattern: Discrete Phase Separation

**What it does**: Breaks a complex multi-agent task into explicit sequential phases, where each phase has different characteristics — different models, tools, context requirements, and quality criteria.

**SE parallel**: SEDA (Staged Event-Driven Architecture). Each stage has its own thread pool, queue, and processing logic. Stages are connected by explicit handoffs. Discrete Phase Separation applies SEDA to agent workflows — each phase is a discrete stage with explicit input/output contracts.

**How it works**:
```
Phase 1 — UNDERSTAND (frontier model, read-only tools)
  Input: user request + codebase
  Output: structured analysis document

Phase 2 — PLAN (frontier model, no tools)
  Input: analysis document
  Output: implementation plan with file-level changes

Phase 3 — IMPLEMENT (mid-tier model, write tools)
  Input: plan + relevant files
  Output: modified files

Phase 4 — VERIFY (mid-tier model, test tools)
  Input: modified files + test suite
  Output: pass/fail + fix suggestions
```

**When to use it**: Any complex task that naturally decomposes into phases with different requirements. The explicit phase boundaries create natural checkpoints for quality gates, cost tracking, and human review.

**Trade-off**: Phase boundaries are rigid. If the implementation phase discovers a flaw in the plan, the system needs a mechanism to loop back — either re-entering the planning phase or allowing limited re-planning within the implementation phase.

## Key Takeaways

1. Orchestrator-Worker is the default multi-agent topology — one agent coordinates, others execute. It maps directly to master-worker distributed systems.
2. Sub-Agent Spawning solves context exhaustion by giving each subtask a fresh context window. The parent gets a compact summary instead of all the raw data.
3. LLM Map-Reduce handles tasks that exceed a single context window by processing chunks in parallel and synthesizing results — the most important pattern for large-scale analysis.
4. Factory over Assistant creates purpose-built, isolated agents for each task type rather than reusing a single general-purpose agent. Cleaner state, better specialization.
5. Hybrid LLM/Code Workflow Coordinator is the most cost-effective production architecture — use deterministic code for predictable steps, agents only where reasoning is required.

## Try This

Implement a simple LLM Map-Reduce:
1. Take a codebase (or a large document) that exceeds the context window.
2. Split it into overlapping chunks (~4000 tokens each, with 500-token overlaps).
3. Map: Ask a cheap model to extract specific information from each chunk (e.g., "list all API endpoints defined in this code").
4. Reduce: Ask a capable model to synthesize all chunk results into a single, deduplicated, organized answer.

Compare the result to what you'd get asking a single model to process as much of the codebase as fits in context. The Map-Reduce result should be more complete (it sees everything) but may have synthesis artifacts at chunk boundaries.

## System Design Question

You're designing a multi-agent system for automated code review. The system receives a pull request diff and must produce a detailed review. Design the orchestration: What agents do you need (planning, reviewing, testing, summarizing)? What topology connects them (pipeline, orchestrator-worker, or hybrid)? Where does deterministic code replace LLM agents? How do you handle the case where the review agent and test agent disagree about whether a change is safe?
