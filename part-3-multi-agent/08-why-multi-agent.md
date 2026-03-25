# Module 8: Why Multi-Agent

**Software engineering parallel**: The monolith-to-microservices transition — you start with a single process doing everything, then split it when the monolith can't scale, when different parts need different characteristics, or when you need independent deployment.

**Patterns covered**: Router Agent / Model Selection, Dual LLM Pattern, Budget-Aware Model Routing with Hard Cost Caps, Progressive Complexity Escalation, Agent Modes by Model Personality

---

## When One Agent Isn't Enough

Modules 4-7 covered a single agent: one system prompt, one reasoning loop, one set of tools. That's sufficient for many tasks. But as task complexity grows, a single agent hits the same limits that monolithic applications hit:

- **Context window exhaustion**: A complex task requires more context than one window can hold — the codebase, the specification, the test output, the conversation history, and the documentation all compete for the same 200K tokens.
- **Capability mismatch**: The same model that's excellent at architecture planning is expensive overkill for renaming a variable. But a single-agent loop uses one model for everything.
- **Latency constraints**: A single agent processes sequentially. When subtasks are independent, serializing them wastes time.
- **Reliability through diversity**: One model can have blind spots. Multiple models catch each other's mistakes.

Multi-agent architecture addresses these limits the same way microservices address monolith limits: by decomposing the problem into specialized, independently-scalable units.

**SE parallel**: This is exactly the microservices motivation. You don't break up a monolith because microservices are cool — you break it up because you need: different scaling characteristics per component, independent deployment, technology heterogeneity (different languages/databases per service), or fault isolation. Every multi-agent pattern in this course maps to a distributed systems pattern you already know.

## The Cost Argument

Module 2 established that different models have radically different cost profiles. As of early 2026:

| Model tier | Input cost (per M tokens) | Output cost (per M tokens) | Best for |
|-----------|--------------------------|---------------------------|----------|
| Frontier (Opus-class) | $15 | $75 | Complex reasoning, architecture |
| Mid-tier (Sonnet-class) | $3 | $15 | General coding, analysis |
| Fast (Haiku-class) | $0.25 | $1.25 | Classification, extraction, simple edits |

A single-agent system using a frontier model for everything is like running every database query on your most expensive cluster. The economic case for multi-agent is often just model routing — sending each subtask to the cheapest model that can handle it.

## Pattern: Router Agent / Model Selection

**What it does**: A lightweight agent (or deterministic logic) classifies incoming tasks and routes them to the appropriate model or specialized agent.

**SE parallel**: Reverse proxy / intelligent load balancer (Nginx, Envoy). The proxy doesn't process requests — it inspects them and routes to the right backend. A router agent inspects the task and routes to the right model.

**How it works**:
```
Router (fast model or heuristic):
  Input: "rename variable foo to bar in auth.py"
  Classification: simple_edit
  Route → Haiku-class model (cheap, fast)

  Input: "redesign the authentication system to support OAuth2 and SAML"
  Classification: architecture
  Route → Opus-class model (expensive, capable)
```

**Implementation approaches**:
1. **Heuristic routing**: Keyword matching, task length, tool requirements. Cheapest but least accurate.
2. **Classifier model**: A fast model classifies the task. Adds one cheap LLM call of latency.
3. **Self-routing**: The model itself estimates difficulty and requests a more capable model if needed. Elegant but the model may not know what it doesn't know.

**Trade-off**: Every routing error costs money — either overpaying (easy task → expensive model) or quality degradation (hard task → cheap model). Calibrating the router on your specific workload using evals (Module 3) is essential.

## Pattern: Dual LLM Pattern

**What it does**: Pairs two models with complementary roles — a "planner" model that reasons about what to do and a "worker" model that executes instructions. Neither sees the full picture; each sees only what it needs.

**SE parallel**: Backend-For-Frontend (BFF) pattern. The BFF is a lightweight API layer that adapts backend responses for a specific frontend client. The Dual LLM Pattern is similar: the planner adapts the user's complex request into simple instructions the worker can execute.

**How it works**: The planner (frontier model) receives the complex task, reasons about it, and produces a series of concrete instructions. The worker (cheaper model) receives each instruction with just enough context to execute it. The planner never touches files directly; the worker never reasons about architecture.

**Scenario**: Planner receives "refactor the payment module to use the strategy pattern." It produces:
1. "Read `payment_processor.py` and list all payment method types"
2. "Create a `PaymentStrategy` interface with method `process(amount, currency)`"
3. "Create concrete strategy classes for each payment type"
4. ...

Each instruction goes to the worker with the relevant file context. The planner sees results and adjusts the plan if needed.

**When to use it**: Tasks where planning requires sophisticated reasoning but execution is routine. Saves 60-80% compared to using a frontier model for everything.

## Pattern: Budget-Aware Model Routing with Hard Cost Caps

**What it does**: Extends the router pattern with explicit cost tracking and hard budget limits. Each task has a budget, and the routing layer ensures the budget isn't exceeded.

**SE parallel**: Rate limiting + tiered pricing. Cloud services don't just route requests — they track consumption and enforce quotas. A $20/hour reserved instance is a hard cost cap. Budget-aware routing applies the same discipline: "this coding session has a $5 budget; route accordingly."

**How it works**: The router tracks cumulative cost (tokens × price per model) across the session. As the budget depletes, routing shifts toward cheaper models. If the budget is nearly exhausted but the task isn't done, the router can: switch to the cheapest model available, ask the user to approve additional budget, or save state and stop.

**Implementation**:
```
session_budget = $5.00
spent = $0.00

for each subtask:
  remaining = session_budget - spent
  if remaining < $0.50:
    route → cheapest model + warn user
  elif subtask.difficulty == "hard" and remaining > $2.00:
    route → frontier model
  else:
    route → mid-tier model
  spent += subtask.actual_cost
```

**Trade-off**: Hard caps prevent runaway costs but can degrade quality at the end of a session. The user experience of "your agent just got dumber because you're out of budget" requires careful UX design (Module 20).

## Pattern: Progressive Complexity Escalation

**What it does**: Starts every task with the cheapest capable model and escalates to more expensive models only when the cheaper one fails or signals uncertainty.

**SE parallel**: Tiered escalation / support levels. L1 support handles common issues; L2 handles complex cases; L3 handles the hardest problems. You don't start every support ticket at L3 — you escalate when needed.

**How it works**:
1. Route task to the fast/cheap model.
2. If it succeeds (passes validation, produces coherent output) → done.
3. If it fails or signals low confidence → re-route to the mid-tier model with the cheap model's partial work as context.
4. If that also fails → escalate to the frontier model.

**When to use it**: High-volume agent workloads where most tasks are simple. If 70% of tasks succeed at the cheap tier, you save 70% of what you'd spend routing everything to the frontier model.

**Trade-off**: Escalation adds latency (the cheap model's failed attempt + the expensive model's successful attempt). For latency-sensitive interactive use, you might prefer routing directly to the right tier. For batch processing, escalation is nearly always the right call.

## Pattern: Agent Modes by Model Personality

**What it does**: Configures different "modes" of agent behavior by pairing different models with different system prompts and tool sets, selectable at runtime.

**SE parallel**: Runtime profiles (development, staging, production). The same application code runs with different configurations depending on the context. Agent modes are runtime profiles: "plan mode" uses a frontier model with architecture-focused prompts and no file-editing tools; "edit mode" uses a mid-tier model with code-specific prompts and full file tools.

**How it works**: Define modes as named configurations:

| Mode | Model | Temperature | Tools | Use case |
|------|-------|-------------|-------|----------|
| Plan | Frontier | 0.7 | Read-only, search | Architecture, design |
| Code | Mid-tier | 0.2 | Read, write, run | Implementation |
| Review | Frontier | 0.3 | Read-only, diff | Code review |
| Quick | Fast | 0.0 | Minimal | Classification, formatting |

The agent (or user) switches modes based on the task phase. Planning shifts to "Plan" mode; implementation shifts to "Code" mode.

**When to use it**: When your agent handles diverse task types within a single session. Modes prevent the "one-size-fits-all" problem where a single configuration is mediocre at everything rather than excellent at specific things.

## The Multi-Agent Decision Framework

Before jumping to multi-agent, ask these questions:

1. **Can a single agent do it within context?** If yes, don't add complexity. Multi-agent has coordination overhead.
2. **Is the bottleneck compute or context?** If the issue is context window exhaustion, consider context management patterns (Module 7) first. If it's model capability, multi-agent helps.
3. **Are subtasks independent?** If yes, parallelization through sub-agents gives linear speedup. If subtasks are tightly coupled, the coordination overhead may exceed the benefit.
4. **Is the cost justification clear?** Multi-agent adds complexity. The cost savings from model routing (typically 50-80%) or the quality improvement from specialized agents should clearly outweigh the engineering cost.

**SE parallel**: This is the same decision framework for microservices. Don't break up the monolith just because you can — break it up when you have a specific scaling, capability, or deployment problem that the monolith can't solve.

## Key Takeaways

1. Multi-agent architecture is motivated by the same forces as microservices: context limits, capability mismatch, latency, and reliability through diversity.
2. Router Agent / Model Selection is the foundational multi-agent pattern — route each task to the cheapest model that can handle it. Most production systems start here.
3. The Dual LLM Pattern pairs a smart planner with a cheap executor, saving 60-80% on tasks where planning is hard but execution is routine.
4. Budget-Aware Routing with Hard Cost Caps prevents runaway spending by tracking consumption and shifting to cheaper models as budgets deplete.
5. Progressive Complexity Escalation starts cheap and escalates only on failure — optimal for high-volume workloads where most tasks are simple.

## Try This

Take a coding task you've previously run on a frontier model. Now run it three ways:
1. **Full frontier**: Entire task on the most capable model.
2. **Dual LLM**: Use the frontier model to produce a step-by-step plan, then execute each step with a cheaper model.
3. **Progressive escalation**: Start with the cheapest model. If the output is wrong (you judge), retry with the mid-tier, then frontier.

Compare: final quality, total token cost, and total latency. The Dual LLM approach should produce comparable quality at significantly lower cost.

## System Design Question

You're designing a multi-agent coding platform for a team of 50 developers. The workload is: 60% simple edits (rename, format, add logging), 25% moderate tasks (add a feature, fix a bug), 15% complex tasks (refactor a module, design an API). Design the routing architecture: how many model tiers, what classification approach, how do you handle misclassification, and what's the expected cost savings vs. routing everything to the frontier model?
