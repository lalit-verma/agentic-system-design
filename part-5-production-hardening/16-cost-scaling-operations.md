# Module 16: Cost, Scaling & Operations

**Software engineering parallel**: Capacity planning and infrastructure operations — the unglamorous work of running services at scale: managing compute budgets, scaling horizontally, handling long-running processes, building async pipelines, and making architectural decisions that keep costs sustainable as usage grows.

**Patterns covered**: No-Token-Limit Magic, Adaptive Sandbox Fan-Out Controller, Asynchronous Coding Agent Pipeline, Extended Coherence Work Sessions, Merged Code + Language Skill Model

---

## The Operations Reality

Modules 14 and 15 covered correctness and security. This module covers the third production concern: running agent systems economically at scale. The patterns here address the operational challenges that emerge when agents move from demo to daily driver — handling tasks too large for any context window, scaling execution horizontally, managing long-running sessions, and making model architecture decisions that balance capability against cost.

Module 2 established the cost model. This module is what you build on top of it.

## Handling Unbounded Work

### No-Token-Limit Magic

**What it does**: Makes the context window limit invisible to the user and the agent by automatically managing content across multiple context windows through summarization, chunking, and continuation.

**SE parallel**: Pagination + streaming. A database doesn't fail when the result set exceeds available memory — it streams results in pages. No-Token-Limit Magic applies the same principle: the agent processes work that far exceeds a single context window by transparently managing context boundaries.

**How it works**: Combine several patterns from earlier modules into an integrated system:
1. **Auto-compaction** (Module 7): Summarize older context when approaching the limit
2. **Stop Hook Auto-Continue** (Module 11): When hitting the turn limit, serialize state and continue in a new session
3. **Progressive Disclosure** (Module 7): Load only relevant file sections, not entire files
4. **Sub-Agent Spawning** (Module 9): Delegate deep research to sub-agents with their own context

The user asks "refactor the entire authentication module." The agent doesn't fail because the module is 50 files and 100K tokens. Instead, it reads files progressively, spawns sub-agents for deep analysis, compacts completed work, and continues across context boundaries — producing the result without ever exposing the context limit to the user.

**Trade-off**: Invisible limits are still limits. Each compaction step loses information. Each continuation boundary is a potential coherence gap. The system works well for tasks that decompose naturally, but struggles with tasks requiring holistic understanding of a very large codebase — where every detail matters simultaneously. For those, you may need to expose the limitation and collaborate with the user on scoping.

### Extended Coherence Work Sessions

**What it does**: Maintains agent coherence and focus across long sessions (hundreds of turns, hours of wall-clock time) through explicit state management, periodic self-checks, and drift detection.

**SE parallel**: Long-running transactions / saga management. A transaction that spans hours needs different mechanisms than one that spans milliseconds — checkpoints, partial commits, and recovery procedures. Extended sessions need the same: the agent must periodically verify it's still on track, hasn't drifted from the original task, and hasn't accumulated contradictory context.

**How it works**:
- **Periodic self-check**: Every N turns, the agent re-reads its task description and working memory (TodoWrite, Module 7) and verifies alignment: "Am I still working on the original task? Have I drifted into a tangent?"
- **Progressive summarization**: Completed sub-tasks are summarized and removed from active context, keeping the working set focused
- **Checkpoint commits**: Partially completed work is committed to a branch at regular intervals, so progress isn't lost if the session fails
- **Drift detection**: If the agent's recent actions don't align with the original task description, it flags the divergence to the user

**When to use it**: Any agent task expected to take more than 30 minutes or 50 turns. Without these mechanisms, agents tend to drift — solving adjacent problems, over-engineering solutions, or losing track of the original objective.

## Scaling Execution

### Adaptive Sandbox Fan-Out Controller

**What it does**: Dynamically scales the number of concurrent agent sandboxes based on workload, managing a pool of isolated execution environments that grow and shrink with demand.

**SE parallel**: Auto-scaling pools (AWS Auto Scaling Groups, Kubernetes Horizontal Pod Autoscaler). When load increases, spin up more instances. When load decreases, terminate excess instances. The fan-out controller does this for agent sandboxes.

**How it works**:
```
Controller loop:
  pending_tasks = queue.depth()
  active_sandboxes = pool.active_count()

  if pending_tasks > active_sandboxes * threshold:
    pool.scale_up(min(pending_tasks - active_sandboxes, max_sandboxes))
  elif active_sandboxes > pending_tasks + buffer:
    pool.scale_down(active_sandboxes - pending_tasks - buffer)

  for sandbox in pool.active():
    if sandbox.idle_time > idle_timeout:
      pool.terminate(sandbox)  # Reclaim resources
```

**Operational concerns**:
- **Cold start**: New sandboxes take time to initialize (clone codebase, install dependencies). Pre-warm a pool of idle sandboxes to reduce latency.
- **Resource limits**: Set per-sandbox limits (CPU, memory, disk) and cluster-wide limits (total sandboxes, total cost/hour).
- **Cleanup**: Sandboxes must be fully cleaned up after each task — no leftover state, no leaked credentials, no lingering processes.

### Asynchronous Coding Agent Pipeline

**What it does**: Processes agent tasks asynchronously through a pipeline of stages, enabling horizontal scaling and decoupling producer (task submission) from consumer (task execution).

**SE parallel**: Async processing pipelines (Celery, SQS + Lambda, Kafka consumers). Work is submitted to a queue, workers pull tasks independently, results are stored for retrieval. The submitter doesn't wait for completion — it receives a task ID and polls or subscribes for results.

**How it works**:
```
Pipeline stages:

1. INTAKE: Task submitted → validated → enriched with context → queued
2. CLASSIFY: Router agent classifies difficulty → selects model tier → assigns budget
3. EXECUTE: Worker sandbox pulls task → agent runs → produces result
4. VALIDATE: Result checked against quality criteria → tests run → review applied
5. DELIVER: Result delivered (PR created, response returned, notification sent)
```

Each stage is independently scalable. A spike in task submissions only increases queue depth — it doesn't overwhelm the execution stage. The validation stage can use a different (cheaper) model than execution. Delivery can be batched.

**When to use it**: Any platform serving multiple users or processing tasks that take more than a few seconds. Interactive single-user agents don't need this. Multi-user platforms do — it's the difference between a CLI tool and a service.

## Model Architecture Decisions

### Merged Code + Language Skill Model

**What it does**: Chooses between using a single model that handles both code and natural language well ("full-stack model") vs. specialized models for each modality — and designs the system accordingly.

**SE parallel**: Full-stack developer vs. specialist teams. A full-stack developer handles both frontend and backend. Specialist teams have dedicated frontend and backend engineers. The trade-off is flexibility vs. depth — and the right choice depends on the complexity of each layer.

**The decision framework**:

**Use a single full-stack model when**:
- Tasks frequently require both code and explanation (coding agents, documentation generators)
- The overhead of routing between models exceeds the cost savings
- Context sharing between code and language understanding is important (the model needs to read code comments to understand code)

**Use specialized models when**:
- Code tasks and language tasks are clearly separable
- A smaller, fine-tuned code model significantly outperforms the general model on code tasks
- Cost optimization is critical and you can route >50% of tasks to a cheaper specialized model

**Trade-off**: The industry is trending toward strong full-stack models, with the model routing approach (Module 8) providing cost optimization without sacrificing capability. As of early 2026, the best approach for most systems is a single frontier model for complex tasks + a fast full-stack model for simple tasks, rather than code-specialist + language-specialist models.

## Operational Best Practices

Beyond named patterns, here are the operational practices that separate toy agents from production systems:

### Cost Attribution and Chargeback

Attribute agent costs to the user, team, or project that initiated the task. Without attribution, agent costs are an uncontrolled shared expense that grows without accountability.

**Implementation**: Tag every API call with the originating user/team/project. Aggregate costs daily. Publish dashboards per team. Set per-team budgets with alerts. This is identical to cloud cost management — the same tools (cost explorers, budget alerts, anomaly detection) apply.

### Capacity Planning

Forecast agent infrastructure needs based on usage trends:
- **Token throughput**: How many tokens/day does your system process? What's the growth rate?
- **Concurrent sessions**: How many simultaneous agent sessions during peak hours?
- **Storage**: How much memory (filesystem state, embeddings, session logs) accumulates per week?
- **Provider rate limits**: Are you approaching your API provider's rate limits? Do you need reserved capacity?

### Graceful Degradation

When infrastructure is stressed, degrade gracefully rather than failing hard:
- **Model fallback**: Primary model rate-limited → fall back to a cheaper model (Module 14's Failover)
- **Feature reduction**: Under load, disable optional features (extended thinking, multi-pass review) to maintain core functionality
- **Queue prioritization**: When the task queue is deep, process high-priority tasks first (Lane-Based Queueing, Module 11)
- **User communication**: Tell users "the system is busy, your task is queued" rather than silently failing

## Key Takeaways

1. No-Token-Limit Magic makes context limits invisible by composing auto-compaction, continuation, progressive disclosure, and sub-agent spawning — the agent handles unbounded work transparently.
2. Extended Coherence Work Sessions prevent drift in long-running agents through periodic self-checks, progressive summarization, and checkpoint commits.
3. Adaptive Sandbox Fan-Out Controller scales agent execution horizontally — pre-warm sandboxes, enforce per-sandbox and cluster-wide limits, and clean up aggressively.
4. Asynchronous Coding Agent Pipelines decouple task submission from execution, enabling independent scaling of each pipeline stage.
5. Cost attribution, capacity planning, and graceful degradation are not patterns — they're operational disciplines that must be in place before scaling.

## Try This

Build a cost attribution dashboard:
1. Instrument an agent to log: model used, input tokens, output tokens, and task type for every API call.
2. Run 50 tasks across 5 simulated "teams" (10 tasks each).
3. Compute: cost per team, cost per task type, average cost per task by model tier.
4. Identify: which team is most expensive? Which task type costs the most? Is the expensive team doing harder work, or using the system inefficiently?

This exercise builds intuition for the operational reality of running agents at scale — cost management is infrastructure management.

## System Design Question

You're designing the operations infrastructure for an agent platform expected to serve 500 developers, each running 10-30 agent sessions per day. Design the full stack: How do you size the sandbox pool (Adaptive Fan-Out)? How do you handle a task that exceeds the context window (No-Token-Limit Magic)? How do you attribute costs to teams (chargeback)? What does your capacity planning model look like — and at what usage level do you need to switch from pure API to hybrid self-hosted? Reference Module 2's build/buy/hybrid analysis.
