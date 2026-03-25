# Module 14: Reliability Engineering

**Software engineering parallel**: Site reliability engineering — you don't just build features, you build the infrastructure that ensures features work correctly at scale: monitoring, testing, rollout procedures, and incident response. The same discipline applies to agents, except the failure modes are nondeterministic.

**Patterns covered**: Structured Output Specification, Schema Validation Retry with Cross-Step Learning, Workflow Evals with Mocked Tools, CriticGPT-Style Code Review, Action Caching & Replay, Failover-Aware Model Fallback, LLM Observability, RLAIF, Canary Rollout and Automatic Rollback, Versioned Constitution Governance, Anti-Reward-Hacking Grader Design, Reliability Problem Map Checklist

---

## Why Agent Reliability Is Different

Traditional software has deterministic bugs: given the same input, you get the same wrong output. Agent failures are stochastic — the same input might succeed 4 out of 5 times and fail once. The same prompt might work perfectly with one model version and break with the next. The test that passed yesterday might fail today because the model's temperature sampling landed differently.

This makes traditional testing necessary but insufficient. You need everything SRE taught you — monitoring, testing, rollout controls, incident response — plus additional infrastructure for nondeterminism.

## Ensuring Correct Output

### Structured Output Specification

**What it does**: Defines the exact schema (JSON Schema, TypeScript types, protobuf) that every agent output must match, and enforces it at the API level through constrained decoding or validation.

**SE parallel**: JSON Schema / protobuf contracts. You don't trust API clients to send valid requests — you validate against a schema and reject malformed payloads. Structured Output Specification does the same for agent output: define the contract, enforce it, reject violations.

Module 3 introduced structured output as a prompting technique. In production, it's infrastructure. Every tool call, every agent response, every inter-agent message has a schema. The runtime validates every output against its schema before processing. A malformed tool call never reaches the tool executor; a malformed response never reaches the user.

**Implementation**: Use provider-level schema enforcement (most APIs support `response_format` with a JSON schema). For inter-agent communication, define schemas as shared contracts. Version schemas alongside your agent code.

### Schema Validation Retry with Cross-Step Learning

**What it does**: When output fails schema validation, automatically retries with the validation error as feedback — and carries forward learnings from the failure to prevent it in subsequent steps.

**SE parallel**: Retry with circuit breaker. A failed HTTP request gets retried with exponential backoff. A circuit breaker prevents retrying indefinitely. Schema Validation Retry applies the same pattern: retry with the error message injected as context, but limit retries and escalate if the pattern persists.

**How it works**: Validation fails → inject the error into the next prompt: "Your output didn't match the schema. Error: field 'severity' must be one of ['low', 'medium', 'high'], got 'moderate'. Please fix." → The model corrects and re-generates. If it fails 3 times, escalate to a more capable model or flag for human review.

**Cross-step learning**: Track which schema violations occur repeatedly. If the model consistently uses "moderate" instead of "medium," add a note to the system prompt: "Severity values are exactly: low, medium, high. Do not use 'moderate'." This prevents future failures before they happen.

### CriticGPT-Style Code Review

**What it does**: Uses a separate model instance as an automated code reviewer that evaluates agent-generated code against quality criteria before it's committed.

**SE parallel**: Automated review bots (SonarQube, CodeClimate). CI pipelines run automated reviews that catch issues before human reviewers see the code. CriticGPT adds an LLM-powered reviewer to the pipeline — it catches logical issues, not just syntactic ones.

**How it works**: After the agent generates code, route it to a reviewer agent with instructions: "Review this code for: correctness, security vulnerabilities, performance issues, and consistency with the codebase style. Produce a structured review." If the reviewer flags critical issues, the code goes back to the agent for revision before being committed.

**Trade-off**: Adds latency and cost (an extra LLM call per code generation). Worth it for production code; overkill for exploratory drafts. Apply it selectively — review code that will be committed, skip code that's part of intermediate reasoning.

### Workflow Evals with Mocked Tools

**What it does**: Tests the agent's reasoning and decision-making by running it against scenarios with mocked tool implementations — tools that return predefined responses instead of executing real operations.

**SE parallel**: Integration tests with mocks. You test your service by mocking downstream dependencies — the database returns canned data, the payment API returns a fake success. Workflow Evals mock the agent's tools: `read_file` returns a predefined file, `run_tests` returns a predefined test failure. You verify the agent makes the right decisions given those inputs.

**How it works**: Define eval scenarios: "Given this file content (mocked read_file) and this test failure (mocked run_tests), the agent should: identify the bug, produce a correct fix, and re-run tests." The mocked tools make the eval deterministic, fast, and reproducible — no filesystem, no real test execution, no nondeterminism from the environment.

**When to use it**: Regression testing for agent behavior. When you change a prompt or model, run the mocked eval suite to verify the agent still makes correct decisions. Mocked evals run in seconds (no real tool execution), so you can run hundreds of them in CI.

## Operational Resilience

### Action Caching & Replay

**What it does**: Caches the results of deterministic tool calls and replays them on subsequent identical calls, avoiding redundant computation and ensuring idempotency.

**SE parallel**: Idempotency keys / request deduplication. An API server that receives the same POST request twice (due to a retry) should produce the same result, not create two resources. Action Caching applies this: if the agent calls `read_file("/src/main.py")` twice in a session, the second call returns the cached result (assuming the file hasn't been modified between calls).

**Why it matters**: Agents frequently re-read the same files, re-run the same searches, and re-compute the same analyses — especially after context compaction (Module 7) drops the earlier results. Caching prevents paying for the same work twice, both in compute cost and context tokens.

### Failover-Aware Model Fallback

**What it does**: When the primary model is unavailable (rate limited, outage, timeout), automatically falls back to an alternative model with appropriate prompt adjustments.

**SE parallel**: Failover routing / active-passive replication. Primary database goes down, queries route to the secondary. Failover-Aware Model Fallback does the same: primary model is unavailable, route to the backup model.

**Implementation considerations**: Different models have different capabilities and prompt formats. The fallback isn't just "use a different model" — it's "use a different model with a prompt adapted to that model's strengths and limitations." Maintain prompt variants per model. Test fallback paths regularly (chaos engineering for agents).

### LLM Observability

**What it does**: Comprehensive monitoring of agent behavior — token usage, latency, error rates, tool-use patterns, reasoning quality, and cost — with alerting on anomalies.

**SE parallel**: OpenTelemetry / Prometheus / Grafana. You instrument your services with metrics, traces, and logs. You build dashboards and set alerts. LLM Observability applies the same discipline to agents.

**What to instrument**:
- **Per-request**: Input/output token counts, latency (TTFT, total), model used, cost, tool calls made
- **Per-session**: Total turns, total cost, task completion status, tools used, errors encountered
- **Per-agent**: Success rate by task type, average cost per task, common failure modes, model utilization
- **Anomaly detection**: Sudden cost spikes (agent looping), latency increases (provider degradation), error rate increases (prompt regression)

**Why it's non-negotiable**: Without observability, you're operating blind. You won't know your agent is looping until a user complains. You won't know a prompt change caused a regression until the next monthly review. Observability is the foundation for every other reliability pattern — you can't fix what you can't see.

### RLAIF (Reinforcement Learning from AI Feedback)

**What it does**: Uses one model to evaluate another model's output, generating automated quality labels at scale. These labels are used to improve prompts, fine-tune models, or filter training data.

**SE parallel**: Automated test feedback loops. Your CI pipeline runs tests that generate pass/fail signals. RLAIF is the same concept at the evaluation level: a judge model generates quality signals that feed into the improvement pipeline (Module 13).

**How it works**: For every agent output, a separate evaluator model scores it on relevant dimensions (correctness, helpfulness, safety). These scores become training signal for Agent RFT (Module 13) or prompt refinement. The evaluator model can process thousands of outputs per hour — far more than human evaluators.

**Trade-off**: The evaluator model has its own biases and blindspots. If the evaluator consistently rates verbose output higher than concise output, the agent learns to be verbose. The evaluator itself needs evaluation — human spot-checks on a sample of RLAIF judgments, looking for systematic bias.

## Deployment Safety

### Canary Rollout and Automatic Rollback

**What it does**: Deploys agent changes (new prompts, new models, new tools) to a small percentage of traffic first, monitors quality metrics, and automatically rolls back if quality degrades.

**SE parallel**: Canary deployments. Deploy the new version to 5% of servers, monitor error rates, gradually increase to 100% if metrics are good, roll back if they're not.

**How it works**: New prompt version → deploy to 5% of sessions → compare eval metrics (success rate, cost, user satisfaction) against the baseline → if statistically indistinguishable or better, increase to 25%, 50%, 100% → if worse, automatic rollback to previous version.

**Why automatic rollback?** Agent regressions can be subtle. A prompt change that improves coding tasks might degrade review tasks. Automatic rollback triggers on any statistically significant quality drop, preventing slow-burn regressions that manual monitoring misses.

### Versioned Constitution Governance

**What it does**: Maintains a versioned, auditable set of behavioral rules (a "constitution") that governs what the agent can and cannot do. Changes to the constitution go through a review and approval process.

**SE parallel**: Policy-as-code / Open Policy Agent (OPA). Infrastructure security policies are defined in code, version-controlled, reviewed, and deployed through the same pipeline as application code. Versioned Constitution Governance treats agent behavioral rules the same way.

**What goes in the constitution**: Safety rules ("never execute code that deletes files outside the project"), quality rules ("always run tests before declaring a task complete"), compliance rules ("never include customer data in logs"). The constitution is injected into the system prompt and enforced by the runtime.

### Anti-Reward-Hacking Grader Design

**What it does**: Designs evaluation rubrics and reward signals that are resistant to gaming — where the agent optimizes for the metric rather than the underlying quality.

**SE parallel**: Fuzzing / property-based testing. Instead of testing specific inputs, test properties that should always hold. Anti-reward-hacking applies the same principle: instead of grading specific outputs, grade properties: "Does the code handle all input types?" rather than "Does the code match this expected output?"

**Why it matters**: If your eval grades based on "test pass rate," the agent might learn to write trivial tests that always pass rather than meaningful tests that verify behavior. If your eval grades based on "user acceptance rate," the agent might learn to write overly verbose, friendly-sounding explanations rather than correct code. The eval rubric shapes agent behavior — design it carefully.

### Reliability Problem Map Checklist

**What it does**: A structured checklist of known failure modes for agentic systems, used during design and review to ensure each failure mode is addressed.

**SE parallel**: Runbooks / operational checklists. Before deploying a new service, you run through a checklist: monitoring configured? Alerts set? Rollback procedure documented? The Reliability Problem Map is the same for agents: a checklist of "did you think about these failure modes?"

**The checklist** (core items):
- [ ] What happens when the model is unavailable? (Failover)
- [ ] What happens when the model returns malformed output? (Schema validation)
- [ ] What happens when the model loops? (Stop conditions, turn limits)
- [ ] What happens when cost exceeds budget? (Budget-aware routing)
- [ ] What happens when the agent modifies the wrong file? (Permission model, sandboxing)
- [ ] What happens when a prompt change causes regression? (Canary rollout, eval suite)
- [ ] What happens when the agent encounters a task type it's never seen? (Escalation, human-in-the-loop)
- [ ] What happens when two agents modify the same file? (Workspace coordination)

This isn't a pattern to implement — it's a discipline to practice. Run through the checklist for every new agent feature, every prompt change, every model upgrade.

## Key Takeaways

1. Structured Output Specification is the first line of defense — enforce schemas at the API level so malformed output never reaches downstream systems. Every inter-agent message needs a contract.
2. LLM Observability is non-negotiable — instrument token usage, latency, error rates, and cost. You cannot improve what you cannot measure.
3. Canary Rollout with Automatic Rollback is how you deploy safely — agent regressions are subtle and stochastic, so automated quality comparison against baseline is essential.
4. Anti-Reward-Hacking requires evaluating properties, not specific outputs — if the eval can be gamed, the agent will game it.
5. The Reliability Problem Map Checklist should be reviewed for every agent change — a structured discipline for thinking about failure modes before they happen in production.

## Try This

Build a minimal observability pipeline for an agent:
1. Instrument an agent session to log: input/output tokens per turn, tool calls made, total cost, total turns, and task outcome (success/failure).
2. Run 20 tasks through the agent. Compute: average cost per task, average turns per task, failure rate, most-used tools.
3. Introduce a prompt regression (remove an important instruction). Run 20 more tasks.
4. Can you detect the regression from the metrics alone, before looking at the outputs?

This exercise demonstrates why observability is the foundation — and how quickly you can detect problems when you have the data.

## System Design Question

You're the SRE for an agent platform serving 10,000 tasks per day. Design the reliability stack: What metrics do you monitor (and what are the alert thresholds)? How do you deploy prompt changes safely? How do you handle the 3am page when the agent's failure rate spikes from 5% to 25%? What's in your incident response runbook for agent-specific failures (model outage, prompt regression, evaluation pipeline failure)?
