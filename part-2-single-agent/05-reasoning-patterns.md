# Module 5: Reasoning Patterns

**Software engineering parallel**: Algorithm design strategies — greedy, divide-and-conquer, dynamic programming, backtracking. Each trades off computation time for solution quality, and the right choice depends on the problem structure.

**Patterns covered**: Chain-of-Thought, ReAct — Reason + Act, Plan-Then-Execute, Tree-of-Thought Reasoning, Graph of Thoughts, Self-Discover, Language Agent Tree Search (LATS), Inference-Time Scaling

---

## Why Reasoning Strategy Matters

In Module 4, the reasoning engine was a black box: the LLM receives context and decides what to do. But *how* it decides varies enormously, and the strategy you choose determines quality, cost, and latency.

A model with no reasoning guidance will take the greedy path — generate the first plausible answer and move on. Sometimes that's fine. For complex, multi-step tasks, it produces shallow answers that miss edge cases. Reasoning patterns are structured strategies that improve the LLM's decision quality, just as choosing quicksort over bubble sort improves performance — at the cost of implementation complexity.

## Pattern: Chain-of-Thought (CoT)

**What it does**: Forces the model to generate intermediate reasoning steps before producing a final answer.

**SE parallel**: Debug logging / showing your work. When a function returns the wrong result, you add print statements to see each intermediate value. CoT does the same thing — it makes the model's reasoning visible and, critically, gives it "scratch space" to work through problems.

**How it works**: Either instruct the model to "think step by step" (zero-shot CoT), or provide examples that demonstrate the reasoning process (few-shot CoT, as covered in Module 3). The model generates reasoning tokens, then the answer.

**When to use it**: Multi-step math, logical deduction, code analysis, any task where the answer depends on intermediate conclusions. For simple factual retrieval or classification, CoT adds cost without improving quality.

**Trade-off**: CoT generates more output tokens (expensive, per Module 2). A model might produce 500 reasoning tokens to arrive at a 10-token answer. But for complex tasks, the accuracy improvement is dramatic — often the difference between usable and unusable output.

**Connection to extended thinking**: Modern models offer built-in CoT via extended thinking (Module 2), where reasoning happens in hidden tokens. The trade-off shifts: you lose visibility into reasoning but gain potentially better quality because the model can reason more freely without formatting constraints.

## Pattern: ReAct — Reason + Act

**What it does**: Alternates between reasoning (thinking about what to do) and acting (using tools), making both visible in the output.

**SE parallel**: The OODA loop — Observe, Orient, Decide, Act. Military decision-making that became the standard model for any feedback-driven system. ReAct is OODA for agents: observe the current state, reason about it, decide on an action, execute it, observe the result, repeat.

**How it works**: On each turn, the model produces:
1. **Thought**: "I need to find the database configuration to understand the connection pooling setup."
2. **Action**: `read_file("/src/config/database.yml")`
3. **Observation**: (tool result injected by the runtime)

Then the next turn starts with the observation in context, and the model produces a new Thought → Action cycle.

**When to use it**: Interactive agent tasks — debugging, exploration, research — where the next action depends on the result of the previous action. ReAct is the default reasoning pattern for most agent implementations. The agent loop from Module 4 is essentially ReAct.

**Trade-off**: Each cycle consumes a full LLM call. A 20-step investigation means 20 round trips to the model, with growing context each time. ReAct is the most flexible pattern but also the most expensive for multi-step tasks.

**Scenario**: A coding agent investigating a performance regression. It reads the slow endpoint, thinks "this query has no index," reads the schema, confirms the missing index, checks if there's an existing migration, then generates the fix. Each step is a Thought-Action-Observation cycle — the agent couldn't plan this sequence in advance because each step depends on what it discovers.

## Pattern: Plan-Then-Execute

**What it does**: Separates planning from execution into two distinct phases. First, the LLM generates a complete plan (list of steps). Then, each step is executed — potentially by a cheaper model or deterministic code.

**SE parallel**: Query planner + executor in databases. PostgreSQL first builds an execution plan (which indices to use, which joins to perform, in what order), then the executor runs that plan. The planner uses statistics and heuristics; the executor follows instructions.

**How it works**:
```
Phase 1 — PLAN (frontier model, higher temperature):
  "To add input validation to the signup endpoint:
   1. Read the current endpoint handler
   2. Identify the input fields and their types
   3. Add validation rules for each field
   4. Write unit tests for the validation
   5. Run tests to verify"

Phase 2 — EXECUTE (cheaper model or same model, low temperature):
  Step 1: read_file("/src/handlers/signup.py")
  Step 2: [analyze, extract fields]
  Step 3: edit_file(...)
  Step 4: write_file(...)
  Step 5: run_tests(...)
```

**When to use it**: Tasks with clear, decomposable structure. Especially effective when the planning step benefits from a powerful model but individual execution steps are routine enough for a cheaper one.

**Trade-off**: The plan may be wrong. If step 3 reveals something unexpected (the endpoint uses a framework-specific validation system the planner didn't anticipate), the agent needs to re-plan. Pure Plan-Then-Execute is brittle; most production systems add a re-planning checkpoint after each step — a hybrid with ReAct.

## Pattern: Tree-of-Thought Reasoning (ToT)

**What it does**: Explores multiple reasoning paths in parallel, evaluates each, and selects the best. Instead of one linear chain, it branches into a tree.

**SE parallel**: Branch-and-bound algorithms. You explore multiple candidate solutions, evaluate their promise, prune the bad ones, and continue exploring the best ones. Also analogous to A/B testing at the reasoning level.

**How it works**: Given a problem, generate N different approaches (branches). For each branch, advance the reasoning one step. Evaluate which branches are most promising (using the LLM as evaluator or a heuristic). Continue only the top-K branches. Repeat until a solution is found.

```
Problem: "Optimize this slow database query"

Branch 1: "Add an index on the WHERE clause columns"
Branch 2: "Rewrite as a materialized view"
Branch 3: "Denormalize the join into a single table"

Evaluate: Branch 1 is simplest and most likely correct → explore first
          Branch 2 is viable for read-heavy workloads → keep
          Branch 3 is high-risk (data consistency) → prune
```

**When to use it**: Problems with multiple valid approaches where the best one isn't obvious upfront. Architecture decisions, complex debugging, optimization problems. Not worth the cost for straightforward tasks.

**Trade-off**: Costs N× more than linear reasoning (multiple LLM calls per step). Only justified for high-stakes decisions where the cost of choosing the wrong approach exceeds the cost of exploring multiple ones.

## Pattern: Graph of Thoughts (GoT)

**What it does**: Extends Tree-of-Thought by allowing branches to merge, forming a directed acyclic graph (DAG) of reasoning. Intermediate results from different branches can be combined.

**SE parallel**: DAG-based workflow engines (Apache Airflow, Prefect). Tasks can fan out, execute in parallel, and fan in — combining results from independent sub-computations.

**How it works**: Like ToT, but after exploring branches independently, you can merge insights. Branch 1 discovers the schema, Branch 2 analyzes the query plan, and a merge step combines both insights to propose an optimization that neither branch would have found alone.

**When to use it**: Complex problems where different aspects can be researched independently and then synthesized. Example: understanding a security vulnerability requires analyzing the code path (branch 1), the deployment configuration (branch 2), and the network topology (branch 3) — then merging all three into a risk assessment.

**Trade-off**: Implementation complexity is high. You need to manage DAG state, handle merge logic, and decide when to merge vs. continue independently. In practice, GoT is more of an architectural principle ("let reasoning paths converge") than a widely productionized pattern. Best practices are still emerging.

## Pattern: Self-Discover

**What it does**: The LLM first introspects on the problem and composes its own reasoning structure — selecting from a library of reasoning modules (e.g., "break into sub-problems," "think about edge cases," "work backward from the goal") before applying them.

**SE parallel**: Runtime query plan optimization. A database optimizer doesn't use the same plan for every query — it inspects the query, considers the available indices and statistics, and composes a custom execution plan. Self-Discover does the same for reasoning: the model inspects the problem and assembles a custom reasoning strategy.

**How it works**:
1. Model is shown a library of reasoning approaches (critical thinking, decomposition, analogy, contradiction-checking, etc.)
2. Model selects which approaches are relevant to the current problem
3. Model structures those approaches into a step-by-step plan
4. Model executes the plan

**When to use it**: Novel or ambiguous problems where the right reasoning approach isn't obvious. Less useful for well-structured tasks where ReAct or Plan-Then-Execute suffice.

**Trade-off**: Adds a meta-reasoning step that costs extra tokens. The payoff depends on problem complexity — for simple tasks, it's overhead; for genuinely novel problems, it can find reasoning strategies that fixed patterns miss.

## Pattern: Language Agent Tree Search (LATS)

**What it does**: Combines Tree-of-Thought with a learned value function — essentially Monte Carlo Tree Search (MCTS) applied to LLM reasoning. Each node in the tree is evaluated not just by the LLM's judgment but by an explicit value estimate that improves over time.

**SE parallel**: Monte Carlo Tree Search, the algorithm behind AlphaGo. Explore the most promising moves, simulate outcomes, backpropagate values, and use accumulated statistics to guide future exploration. LATS applies this to agent decision-making.

**How it works**: At each decision point, expand multiple candidate actions. Simulate each path forward (either by actually executing or by asking the LLM to predict the outcome). Backpropagate success/failure signals to update value estimates. Over iterations, the search focuses on the most promising branches.

**When to use it**: High-stakes, multi-step tasks where mistakes are expensive and you can afford the computational overhead. Code generation benchmarks have shown significant improvement with LATS over single-pass reasoning.

**Trade-off**: Extremely expensive — potentially 10-50× more LLM calls than ReAct for the same task. Justified only when the value of getting the right answer significantly exceeds the compute cost. Best practices for when to deploy LATS vs. simpler patterns are still being established in production systems.

## Pattern: Inference-Time Scaling

**What it does**: Dynamically adjusts how much computation the model spends on a problem based on its difficulty. Easy problems get fast, cheap inference. Hard problems get extended thinking, multiple attempts, or tree search.

**SE parallel**: Horizontal autoscaling / compute-on-demand. Your system doesn't run the same number of instances for 100 requests/second and 10,000 — it scales up when load increases and scales down when it drops. Inference-Time Scaling is the same principle applied to thinking: scale up reasoning compute for hard problems.

**How it works**: Classify the task difficulty (using a lightweight model, heuristics, or the model's own confidence estimate). Then select the appropriate strategy:

| Difficulty | Strategy | Cost |
|-----------|----------|------|
| Trivial | Direct answer, no CoT | 1× |
| Simple | Brief CoT | 2-3× |
| Moderate | Extended thinking | 5-10× |
| Hard | Tree-of-Thought or multiple attempts | 10-50× |
| Very hard | LATS or best-of-N with verification | 50-100× |

**When to use it**: Any production agent. The question isn't whether to use inference-time scaling, but how to implement the difficulty classifier. Common approaches: let the model self-report confidence (unreliable for edge cases), use a cheaper model to pre-classify (adds latency), or use task metadata (known task types → known difficulty).

**Trade-off**: The difficulty classifier itself has error rates. If it misclassifies a hard problem as easy, you get a bad answer cheaply. If it misclassifies an easy problem as hard, you overpay. The sweet spot is calibrating the classifier on your specific workload — another instance where evals (Module 3) matter.

## Choosing a Reasoning Strategy

No single reasoning pattern is best for all tasks. Here's a decision framework:

- **Default**: ReAct. It's the most flexible and works well for 80% of agent tasks.
- **Decomposable tasks with clear structure**: Plan-Then-Execute. Reduces cost by using cheaper models for execution.
- **Accuracy-critical with budget**: Tree-of-Thought. Explore multiple approaches, pick the best.
- **Production cost optimization**: Inference-Time Scaling. Match reasoning depth to task difficulty.
- **Research/advanced applications**: LATS or Graph of Thoughts. High cost but best quality for complex problems.

Most production agents use ReAct as the primary loop with Inference-Time Scaling to control costs — enabling extended thinking only when the model signals uncertainty or the task is known to be complex.

## Key Takeaways

1. Chain-of-Thought is the foundational reasoning technique — it trades output tokens for accuracy and should be the baseline for any non-trivial task.
2. ReAct (Reason + Act) is the default agent loop pattern — alternating thinking and tool use. Most agent implementations are ReAct under the hood.
3. Plan-Then-Execute separates strategy from tactics, enabling cheaper models for execution — but plans are brittle and need re-planning checkpoints.
4. Tree and graph reasoning patterns (ToT, GoT, LATS) trade compute for quality by exploring multiple paths. They're 10-100× more expensive and currently justified mainly for high-stakes decisions.
5. Inference-Time Scaling is the meta-pattern — match reasoning compute to problem difficulty. Every production agent needs this to manage cost.

## Try This

Take a moderately complex coding task (e.g., "refactor this function to handle the edge case where the input list is empty and the cache is cold"). Run it three ways:
1. **Direct**: No reasoning guidance, just ask for the code.
2. **Chain-of-Thought**: Ask the model to think step by step before writing code.
3. **Plan-Then-Execute**: Ask the model to first produce a numbered plan, then execute each step.

Compare: correctness (does it handle the edge case?), code quality, token usage, and latency. You'll likely find that CoT and Plan-Then-Execute produce better results but cost 2-5× more — the fundamental trade-off this module is about.

## System Design Question

You're building a coding agent that handles both simple tasks ("rename this variable") and complex tasks ("refactor this module to use the strategy pattern"). Design an Inference-Time Scaling system: How would you classify task difficulty? What reasoning strategy would you apply at each level? How would you handle the case where the difficulty classifier is wrong — a hard task gets routed to the simple path and fails?
