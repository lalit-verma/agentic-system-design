# Module 12: Feedback Loops

**Software engineering parallel**: CI/CD and observability — the mechanisms that tell you whether your system is working correctly, catch regressions before users do, and create the data you need to improve.

**Patterns covered**: Reflection Loop, Self-Critique Evaluator Loop, Evaluator-Optimizer, Coding Agent CI Feedback Loop, Background Agent with CI Feedback, Spec-As-Test Feedback Loop, Rich Feedback Loops > Perfect Prompts, Incident-to-Eval Synthesis, Inference-Healed Code Review Reward, Tool Use Incentivization via Reward Shaping

---

## Why Feedback Is the Bottleneck

Module 2 established the economics: a wasted agent session — one where the agent goes down the wrong path for 30 turns before producing unusable output — costs real money. The difference between a $0.50 session and a $15 session is often whether the agent caught its mistake early.

Feedback loops are the mechanisms that catch mistakes early, redirect the agent, and — over time — make the agent less likely to make those mistakes again. Without feedback, an agent is an open-loop system: it takes an action and hopes for the best. With feedback, it's a closed-loop system: it takes an action, observes the result, evaluates quality, and adjusts.

Every well-engineered system has feedback. Databases have query planners that learn from statistics. CI pipelines catch bugs before they ship. Monitoring alerts engineers before users notice problems. Agentic systems need the same infrastructure — adapted to the unique characteristics of nondeterministic, LLM-powered execution.

## Group 1: Within-Session Feedback

These patterns improve the agent's output during a single session by evaluating and correcting its own work.

### Reflection Loop

**What it does**: After producing output, the agent explicitly evaluates its own work and revises it before presenting the final result. Think-do-review as a structured cycle.

**SE parallel**: TDD red-green-refactor. Write a failing test (think), make it pass (do), refactor (review). The refactor step is the reflection — you don't ship the first thing that works, you improve it. Reflection applies the same discipline to agent output.

**How it works**:
```
Step 1 — Generate: Agent produces initial code/answer
Step 2 — Reflect: "Review what I just wrote. Are there bugs?
  Does it handle edge cases? Is it consistent with the codebase style?"
Step 3 — Revise: Agent fixes identified issues
Step 4 — (Optional) Repeat steps 2-3 until satisfied or budget exhausted
```

**When to use it**: Any task where first-draft quality is insufficient — complex code, architecture decisions, user-facing documentation. For simple edits (rename, format), reflection adds cost without value.

**Trade-off**: Each reflection cycle is an additional LLM call with the full context. Two rounds of reflection roughly triples the cost of a single generation. The quality improvement must justify the spend — and it usually does for non-trivial tasks, but diminishing returns set in quickly. More than 2-3 reflection rounds rarely helps.

### Self-Critique Evaluator Loop

**What it does**: A separate evaluation step (using the same or a different model) grades the agent's output against explicit quality criteria and triggers revision only when the grade is below threshold.

**SE parallel**: Code review / static analysis. Your CI pipeline runs linters and static analyzers — if they fail, the build fails and you fix the issues. Self-critique is an automated reviewer that evaluates output against defined criteria (correctness, completeness, style) and rejects substandard work.

**How it differs from Reflection**: Reflection is the agent reviewing its own work with a vague "is this good?" prompt. Self-critique uses a structured rubric: "Score this code 1-5 on: correctness, edge case handling, readability. If any score < 3, explain why and suggest fixes." The structured evaluation produces more reliable quality signals.

**Implementation**: Define a rubric as structured output:
```json
{
  "correctness": {"score": 4, "issues": []},
  "edge_cases": {"score": 2, "issues": ["empty input not handled"]},
  "readability": {"score": 4, "issues": []},
  "verdict": "revise"
}
```

If verdict is "revise," the agent receives the critique and produces a revised version. If "accept," the output is final.

### Evaluator-Optimizer

**What it does**: Pairs two agents in a persistent loop: one generates output (the optimizer), the other evaluates it (the evaluator). The evaluator's feedback drives the optimizer's next iteration. They iterate until the evaluator approves.

**SE parallel**: TDD with optimization / adversarial testing. The test suite is the evaluator — it defines what "correct" means. The code is the optimizer — it keeps changing until the tests pass. The pairing creates a productive tension between generation and evaluation.

**How it works**: The evaluator has the specification, acceptance criteria, and test cases. The optimizer has the tools and implementation capability. Each round:
1. Optimizer produces/revises the implementation
2. Evaluator grades it against criteria
3. If passing → done. If failing → evaluator explains what's wrong
4. Optimizer revises based on feedback

**When to use it**: Tasks with clear, testable success criteria. Code that must pass a test suite, documentation that must cover specific topics, configurations that must meet compliance requirements. Less useful when "quality" is subjective.

**Trade-off**: Convergence isn't guaranteed. If the evaluator's criteria are too strict or contradictory, the optimizer can loop indefinitely. Always include a maximum iteration count and a "good enough" threshold.

## Group 2: External Feedback Signals

These patterns connect the agent to real-world feedback — test suites, CI systems, and production signals.

### Coding Agent CI Feedback Loop

**What it does**: The agent writes code, runs the test suite (or CI pipeline), reads the results, and uses failures to guide its next action. The CI system is the feedback signal.

**SE parallel**: CI/CD pipelines — the most fundamental feedback loop in software engineering. Write code, push, CI runs, read the results, fix failures. The agent does exactly this, but autonomously and within a single session.

**How it works**:
```
1. Agent writes code changes
2. Agent runs: `pytest tests/` or triggers CI
3. Agent reads test output
4. If all pass → done
5. If failures → agent reads failing tests, analyzes errors,
   produces fixes, goes to step 2
```

**Why it's powerful**: Test results are the most reliable feedback signal available. Unlike self-critique (where the model might miss its own errors), test failures are objective. A failing assertion is unambiguous: the code doesn't do what the test expects.

**Trade-off**: Only works when test coverage is good. If the test suite doesn't cover the edge case the agent introduced, the feedback loop won't catch the bug. "All tests pass" doesn't mean "the code is correct" — it means "the code is consistent with the existing tests."

### Background Agent with CI Feedback

**What it does**: Extends the CI feedback loop to asynchronous, background execution. The agent runs in the background, submits code, waits for CI results (which may take minutes), and continues based on the outcome.

**SE parallel**: Async workers + webhooks. A background job submits a request to an external system and registers a webhook callback. When the result arrives, the job resumes. Background agents do the same: submit a PR, register for CI results, and resume when CI completes.

**When to use it**: When CI takes too long for synchronous execution (minutes to hours). The agent can work on other subtasks while waiting, or simply idle at low cost until the webhook fires.

**Implementation consideration**: The agent must serialize its state before waiting (Proactive Agent State Externalization, Module 7) and restore it when CI results arrive. This is the Stop Hook Auto-Continue pattern (Module 11) triggered by an external signal rather than a turn limit.

### Spec-As-Test Feedback Loop

**What it does**: The specification itself functions as the test — the agent writes code to satisfy a specification, and the specification is checked programmatically against the output.

**SE parallel**: Contract testing / BDD (Behavior-Driven Development). In BDD, the specification ("Given X, When Y, Then Z") is simultaneously the requirement and the test. Spec-As-Test applies this: the agent receives a specification that is machine-checkable, and the feedback loop checks the output against the spec.

**How it works**: The specification is expressed in a verifiable format — JSON Schema for API contracts, type signatures for functions, property-based test assertions. The agent generates the implementation, the spec is checked automatically, and failures drive revision.

**When to use it**: API development (OpenAPI specs), data pipelines (schema contracts), typed languages (type checking is a spec). Anywhere the specification can be mechanically verified against the output.

## Group 3: Systemic Feedback Patterns

These patterns address feedback at the system level — how the overall agent platform improves over time.

### Rich Feedback Loops > Perfect Prompts

**What it does**: Invests in building fast, informative feedback mechanisms rather than perfecting prompts. The insight: a mediocre prompt with excellent feedback produces better results than a perfect prompt with no feedback.

**SE parallel**: Observability-driven development. Instead of trying to write bug-free code, invest in monitoring, logging, and alerting that catch bugs fast. The cost of a fast-caught bug is lower than the cost of trying to prevent every possible bug through perfect code.

**Applied to agents**: Instead of spending weeks perfecting a system prompt, ship a good-enough prompt with: comprehensive test suites the agent can run, linters that catch common mistakes, type checkers that enforce contracts, and structured evaluation rubrics. Each of these feedback signals tells the agent what's wrong, enabling self-correction that no amount of prompt optimization can replace.

**Why this is a paradigm shift**: Most agent development focuses on prompt engineering — making the agent "smarter" through better instructions. This pattern argues the higher-leverage investment is making the agent's environment more informative — better tools, better tests, better feedback.

### Incident-to-Eval Synthesis

**What it does**: When an agent makes a mistake in production, the incident is automatically converted into an eval test case — ensuring the same mistake never happens again.

**SE parallel**: Post-mortems → regression tests. When a production incident occurs, a good engineering team writes a regression test that reproduces the bug. If that test ever fails again, CI catches it before deployment. Incident-to-Eval does the same for agents: every agent failure becomes a test case for future agent evaluation.

**How it works**:
1. Agent produces bad output (detected by user feedback, test failure, or monitoring)
2. Extract: the input that triggered the failure, the bad output, and the expected correct output
3. Add this triplet (input, bad_output, expected_output) to the eval suite
4. Run all future prompt/model changes against this growing eval suite
5. Reject changes that regress on previously-fixed failures

**Why it compounds**: Each incident makes the eval suite stronger. After 100 incidents, you have 100 test cases that represent real failure modes — far more valuable than synthetically-generated evals. Over time, the eval suite becomes the most important quality asset in the system.

### Inference-Healed Code Review Reward

**What it does**: Uses code review outcomes (approved, changes requested, rejected) as reward signals to improve future agent-generated code. The agent learns which coding patterns get approved and which get sent back.

**SE parallel**: Reward shaping in ML / learning from code review feedback. Senior developers learn from code reviews — they internalize what reviewers care about and produce code that needs fewer revisions over time. This pattern formalizes that learning for agents.

**How it works**: Track code review outcomes for agent-generated code. Aggregate patterns: "Code that includes error handling gets approved 90% of the time. Code without error handling gets changes-requested 60% of the time." Feed these patterns back into the agent's system prompt or few-shot examples.

**Trade-off**: Review quality varies — different reviewers have different standards. The signal is noisy. Requires enough data to be statistically meaningful.

### Tool Use Incentivization via Reward Shaping

**What it does**: Shapes the agent's tool-use behavior by rewarding desired tool patterns and penalizing undesired ones — encoded in the prompt, not in model weights.

**SE parallel**: A/B testing to optimize behavior. Test different tool-use strategies, measure which produces better outcomes, and encode the winner in the system prompt.

**How it works**: Add prompt-level guidance based on measured outcomes: "When searching for code, prefer Grep over Bash — Grep produces structured output that's easier to parse (based on 85% success rate vs 60%)." These steering hints (Module 6's Tool Use Steering) are derived from empirical measurement rather than intuition.

**When to use it**: Any production agent where you can measure outcome quality by tool-use pattern. The feedback loop is: measure → analyze → encode → deploy → measure again.

## Key Takeaways

1. Reflection and Self-Critique are the baseline: every non-trivial agent output should be reviewed before delivery. Self-critique with structured rubrics is more reliable than open-ended reflection.
2. CI feedback loops are the most powerful feedback mechanism — test failures are unambiguous, objective signals. Invest in test coverage for agent-touched code.
3. Rich Feedback Loops > Perfect Prompts: invest in making the agent's environment informative (tests, linters, type checkers) rather than perfecting the prompt.
4. Incident-to-Eval Synthesis compounds — every production failure becomes a regression test, making the system permanently stronger.
5. Reward signals from code reviews and tool-use outcomes shape agent behavior empirically rather than through prompt intuition.

## Try This

Implement a Self-Critique loop:
1. Ask a model to generate a function that parses a complex date format.
2. Then ask the same model (in a separate call) to evaluate the function against a rubric: correctness, edge cases, readability — each scored 1-5.
3. If any score < 4, feed the critique back and ask for a revision.
4. Compare: the first-draft function vs. the post-critique function. Run both against 10 edge-case inputs.

Track: how often does critique catch real bugs? How often does it flag non-issues? What rubric criteria produce the most useful feedback?

## System Design Question

You're building the feedback infrastructure for a coding agent platform. The agent generates ~500 code changes per day across 50 repositories. Design the feedback system: What signals do you collect (test results, review outcomes, deployment success, user satisfaction)? How do you turn those signals into agent improvements? How do you handle conflicting signals (tests pass but reviewer rejects)? How do you measure whether the feedback system is actually improving agent quality over time?
