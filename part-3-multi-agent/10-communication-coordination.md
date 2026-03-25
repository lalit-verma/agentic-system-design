# Module 10: Communication & Coordination

**Software engineering parallel**: Distributed consensus and collaboration protocols — how independent processes agree on results, resolve conflicts, and produce outputs that are better than what any single process could achieve.

**Patterns covered**: Ensemble / Voting Agent, Iterative Multi-Agent Brainstorming, Opponent Processor / Multi-Agent Debate, Recursive Best-of-N Delegation, Self-Rewriting Meta-Prompt Loop, Feature List as Immutable Contract, Specification-Driven Agent Development, Multi-Model Orchestration for Complex Edits, Parallel Tool Call Learning, Explicit Posterior-Sampling Planner, Swarm Migration Pattern

---

## Beyond Topology: How Agents Collaborate

Module 9 defined the organizational structure — who directs whom. This module addresses the harder question: how do agents communicate, reach agreement, and produce results that exceed what any individual agent can do?

In distributed systems, the hardest problems are consensus and coordination. The same is true for multi-agent systems: getting two LLMs to agree on an approach, combine their work coherently, or catch each other's mistakes requires explicit protocols.

## Group 1: Quality Through Diversity

These patterns use multiple agents to improve output quality beyond what a single agent can achieve.

### Ensemble / Voting Agent

**What it does**: Runs the same task on N agents (same or different models) and combines their outputs through voting, averaging, or majority selection.

**SE parallel**: Quorum reads / consensus protocols. In a distributed database, you read from multiple replicas and take the majority answer — this tolerates individual node failures. Ensemble agents tolerate individual model errors.

**How it works**: Send the same prompt to 3-5 agents. For classification tasks, take the majority vote. For generation tasks, use a judge agent to select the best output, or merge the best parts of each.

**When to use it**: High-stakes decisions where the cost of being wrong exceeds the cost of N× inference. Code review (multiple reviewers catch different bugs), security analysis (different models have different blindspots), or any task where you need confidence in the answer.

**Trade-off**: Costs N× more. Only justified when accuracy matters more than cost. For routine tasks, a single good model is cheaper and nearly as accurate.

### Opponent Processor / Multi-Agent Debate

**What it does**: Assigns agents opposing roles — one proposes, another critiques — forcing adversarial examination of ideas.

**SE parallel**: Chaos engineering / red teams. You don't test your system by asking the team that built it; you test it with a red team whose job is to break it. Multi-agent debate is automated red teaming: one agent proposes a solution, another agent's explicit job is to find flaws.

**How it works**:
```
Agent A (proposer): "Here's my implementation of the rate limiter..."
Agent B (critic): "This has a race condition — two requests hitting
  different replicas at the same instant both pass the check..."
Agent A (revised): "Good catch. Here's the fix using a distributed
  counter with atomic increment..."
Agent B (critic): "The atomic increment adds latency. Consider
  using a sliding window instead..."
```

**When to use it**: Architecture decisions, security reviews, complex code where subtle bugs are likely. Not worth the overhead for simple tasks.

### Recursive Best-of-N Delegation

**What it does**: Generates N candidate solutions, evaluates them, takes the best, and recursively refines it through further N-way generation.

**SE parallel**: Tournament selection in genetic algorithms. Each round, candidates compete; winners advance; losers are discarded. Over multiple rounds, quality converges upward.

**How it works**: Round 1 — generate 5 implementations. Evaluate each (run tests, check quality). Take the top 2. Round 2 — generate 3 variations of each winner. Evaluate. Take the best. Repeat until quality threshold is met or budget is exhausted.

**Trade-off**: Exponentially expensive. 5 candidates × 3 rounds = 15 generations. Justified only for high-value outputs where the marginal improvement in quality has significant impact — a core algorithm, a public API design, a security-critical component.

### Iterative Multi-Agent Brainstorming

**What it does**: Multiple agents contribute ideas in rounds, building on each other's suggestions, with a moderator that synthesizes and directs.

**SE parallel**: The RFC (Request for Comments) process. An author proposes, reviewers comment, the author revises, new reviewers add perspective. Each round improves the proposal by incorporating diverse viewpoints.

**How it works**: Round 1 — Agent A proposes an architecture. Round 2 — Agents B and C review it, each from a different perspective (performance, security). Round 3 — Agent A revises based on feedback. Round 4 — Final review. The moderator agent decides when the proposal is good enough.

**When to use it**: Design decisions with multiple valid approaches and important trade-offs. Less useful for tasks with clear right answers.

### Explicit Posterior-Sampling Planner

**What it does**: Generates multiple plans by sampling from the model's distribution (higher temperature), then scores each plan against quality criteria and selects the highest-scoring one.

**SE parallel**: Probabilistic load balancing / weighted random selection with scoring. Instead of always choosing the greedy-best, sample multiple candidates, evaluate rigorously, and select based on evaluation scores.

**How it works**: Generate 5-10 plans at temperature 0.8 (more diverse than greedy). Score each on: completeness, feasibility, risk, estimated cost. Select the plan that best balances these criteria. This often produces better plans than a single greedy generation because the diversity surfaces approaches the greedy path would miss.

**Trade-off**: N× more planning cost. Useful when the cost of a bad plan (failed execution, wasted tokens) exceeds the cost of generating multiple plans.

## Group 2: Contracts and Coordination Protocols

These patterns define how agents agree on interfaces, share work, and maintain coherence.

### Feature List as Immutable Contract

**What it does**: Defines the expected output as a structured, versioned feature list that all agents reference. The contract doesn't change during execution — agents implement against it, not against evolving requirements.

**SE parallel**: Protobuf schemas / API contracts. You define the interface first, then both client and server implement against it independently. Feature List as Immutable Contract applies the same principle: the orchestrator defines what must be produced, and workers implement against that specification.

**Why immutable?** LLMs are susceptible to scope creep — a worker agent might "helpfully" add features the orchestrator didn't request, breaking assumptions in other agents' work. Immutable contracts prevent this.

### Specification-Driven Agent Development

**What it does**: The orchestrator produces a detailed specification (inputs, outputs, behavior, edge cases) before any implementation begins. Workers implement against the spec, not against a vague description.

**SE parallel**: Spec-first API development (OpenAPI/Swagger first, then implementation). Writing the spec forces you to think through edge cases before writing code. Specification-driven development forces the planner to be precise before workers start executing.

**How it differs from Plan-Then-Execute (Module 5)**: Plan-Then-Execute produces a task list ("step 1, step 2"). Specification-Driven produces a formal specification ("input: X, output: Y matching schema Z, edge case: if X is empty, return []"). The spec is more rigorous and testable.

### Multi-Model Orchestration for Complex Edits

**What it does**: Coordinates multiple models to make coherent changes across multiple files, ensuring consistency and resolving conflicts.

**SE parallel**: Saga pattern in distributed transactions. When a business operation spans multiple services, a saga coordinates the steps and handles compensation (rollback) if any step fails. Multi-model orchestration is a saga across files: edit A, then B, then C — if C fails, ensure A and B are still consistent.

**How it works**: The orchestrator maintains a dependency graph of file changes. Changes are applied in dependency order. After each change, a validation check ensures consistency (types still match, imports are correct, tests pass). If validation fails, the orchestrator rolls back and replans.

### Parallel Tool Call Learning

**What it does**: Tracks which tool calls can safely run in parallel (independent) vs. must run sequentially (dependent), learning from execution history.

**SE parallel**: Concurrent request optimization. A load testing tool learns which API endpoints are independent and can be hit simultaneously vs. which have ordering dependencies. Parallel Tool Call Learning applies this to agent tool use across multiple agents or within a single orchestrated workflow.

**How it works**: Track pairs of tool calls and whether they produce conflicts (file write + file read to the same file = dependent). Over time, build a dependency model: `read_file` calls are always independent of each other; `edit_file` and `read_file` on the same file are dependent. Use this to automatically parallelize where safe.

## Group 3: Adaptive and Self-Modifying Systems

### Self-Rewriting Meta-Prompt Loop

**What it does**: An agent evaluates its own performance, identifies weaknesses in its prompts, and rewrites them to improve future execution.

**SE parallel**: JIT compilation. A JIT compiler observes which code paths are hot, compiles them to optimized native code, and replaces the interpreted version. The self-rewriting loop observes which tasks fail, analyzes why, and optimizes the prompts that produce those failures.

**How it works**: Run task → evaluate output → if quality is below threshold, analyze the failure → identify what prompt instruction would have prevented it → update the system prompt → run next task with improved prompt.

**Trade-off**: This is powerful but risky. A bad self-modification can degrade future performance (the prompt equivalent of a buggy optimization). Production systems should version prompts and roll back if quality drops. Best practices are still emerging — treat this as experimental.

### Swarm Migration Pattern

**What it does**: Migrates a workload from one agent configuration to another without downtime, running both configurations in parallel during the transition.

**SE parallel**: Blue-green deployment. Both the old and new versions run simultaneously. Traffic gradually shifts from blue (old) to green (new). If green fails, traffic shifts back to blue. Swarm migration applies this to agent configurations — gradually shifting task routing from the old prompt/model/tool configuration to the new one.

**How it works**: Deploy the new agent configuration alongside the old. Route a small percentage of tasks to new (canary). Compare quality metrics. If new is at least as good, increase the percentage. If new is worse, roll back. This allows safe evolution of agent behavior in production.

**When to use it**: Any production agent system that needs to evolve — new models, new prompts, new tools. Swapping agent configurations without migration is like deploying to production without a canary: it works until it doesn't, and then it's catastrophic.

## Key Takeaways

1. Ensemble / Voting agents improve accuracy by running multiple agents and taking the consensus — the multi-agent equivalent of quorum reads. Use for high-stakes decisions where the cost of being wrong justifies N× compute.
2. Opponent Processor / Debate forces adversarial examination of proposals, catching flaws that a single agent misses. Automated red teaming for design and security decisions.
3. Feature List as Immutable Contract and Specification-Driven Development prevent scope creep and ensure coherence when multiple agents work on the same task.
4. Multi-Model Orchestration for Complex Edits applies the saga pattern to multi-file changes — coordinate, validate, and rollback if needed.
5. Swarm Migration enables safe evolution of agent configurations in production through blue-green deployment of agent behavior.

## Try This

Implement a simple debate pattern:
1. Give Agent A a coding task and collect its solution.
2. Give Agent B the same task plus Agent A's solution, with instructions to find bugs or improvements.
3. Give Agent A Agent B's critique, with instructions to address it.
4. Compare: the original solution vs. the post-debate solution.

Run this on 5 different tasks. Track: how often does the debate improve the solution? How often does it make it worse (over-engineering from the critique)? What types of tasks benefit most?

## System Design Question

You're designing a multi-agent code review system for a team that deploys 50 PRs per day. Design the coordination: Which agents review (security, performance, style, correctness)? How do they avoid contradictory feedback? How do you handle disagreements between agents? How do you evolve the review criteria over time without breaking the system (hint: Swarm Migration)?
