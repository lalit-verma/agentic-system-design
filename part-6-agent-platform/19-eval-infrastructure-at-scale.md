# Module 19: Eval Infrastructure at Scale

**Software engineering parallel**: CI/CD infrastructure — not the tests themselves, but the systems that run tests at scale: test runners, result aggregation, flakiness detection, coverage tracking, performance benchmarking, and the dashboards that make test results actionable. This module builds the equivalent for agent evaluation.

**Patterns covered**: AI Web Search Agent Loop

---

## Why Eval Infrastructure Is the Moat

Module 3 introduced evals as "test suites for LLMs." Module 12 showed how feedback loops generate eval cases. Module 14 used evals for canary rollout decisions. This module covers the engineering challenge of running evals at scale — the infrastructure that makes the entire quality feedback loop work.

Here's the claim: **eval infrastructure is the single most important investment in an agent platform.** Not the models. Not the prompts. Not the tools. The eval infrastructure. Here's why:

- Models improve continuously. When a new model drops, you need to evaluate it against your workload within hours, not weeks.
- Prompts change frequently. Every prompt change needs regression testing across hundreds of scenarios.
- The eval suite grows continuously (Incident-to-Eval Synthesis, Module 12). Last month you had 200 eval cases; this month you have 350.
- Results must be comparable across time. "Did we get better this quarter?" requires consistent evaluation methodology.

Without eval infrastructure, every model change is a gamble. Every prompt change is hope-based engineering. With it, you have data-driven quality management — the same discipline that CI/CD brought to software delivery.

**SE parallel**: Consider what software looked like before CI/CD: developers ran tests manually, deployments were scary, and regressions were found by users. CI/CD infrastructure — automated test runners, coverage reports, deployment gates — transformed software quality. Eval infrastructure does the same for agents.

## The Eval Pipeline Architecture

```
Eval Pipeline:

┌──────────┐    ┌───────────┐    ┌──────────┐    ┌───────────┐
│  Eval    │───▶│ Execution │───▶│ Grading  │───▶│ Reporting │
│  Suite   │    │ Engine    │    │ System   │    │ & Gating  │
└──────────┘    └───────────┘    └──────────┘    └───────────┘
     │                │                │                │
     ▼                ▼                ▼                ▼
  Case mgmt      Sandboxing       Judge models    Dashboards
  Versioning     Parallelism      Rubrics         Alerts
  Sampling       Replay           Human review    Deploy gates
```

Four stages, each with its own engineering challenges.

## Stage 1: The Eval Suite

### Case Design

An eval case defines: an input (what the agent receives), an environment (what tools and context are available), and success criteria (how to judge the output).

**Types of eval cases**:

1. **Unit evals**: Test a single agent decision. "Given this file content and this error message, does the agent identify the correct bug?" No real tool execution needed (Workflow Evals with Mocked Tools, Module 14).

2. **Integration evals**: Test a multi-step agent workflow. "Given this GitHub issue, does the agent produce a working fix that passes the test suite?" Requires real tool execution in a sandbox.

3. **Regression evals**: Derived from real incidents (Incident-to-Eval Synthesis, Module 12). "The agent previously failed on this exact scenario. Does it still fail?"

4. **Adversarial evals**: Test robustness. "Given this prompt injection attempt embedded in a code comment, does the agent follow the malicious instruction?" Security testing for agents.

5. **Capability evals**: Test frontier capabilities. "Can the agent correctly refactor a module with 10 interdependent files?" These push the boundary of what's possible and track progress over model generations.

### Case Management

At scale, you manage hundreds to thousands of eval cases:

**Versioning**: Eval cases are code — version-controlled, reviewed, and tagged. When the eval criteria change (e.g., you raise the bar for "acceptable code quality"), you version the change so historical comparisons remain valid.

**Tagging and categorization**: Cases are tagged by: capability (coding, review, debugging), difficulty (easy, medium, hard), task type (refactor, bugfix, feature), and source (synthetic, incident-derived, user-submitted). This enables filtering: "Run all medium-difficulty refactoring evals."

**Sampling**: You can't run every eval case on every change — at 1,000 cases × 5 minutes each, that's 83 hours of compute. Instead, sample strategically:
- **Always run**: Regression cases from real incidents (highest value)
- **Stratified sample**: Representative sample across capability tags
- **Targeted run**: Cases relevant to the specific change (prompt change for code review → run code review evals)

**SE parallel**: Test suite management at scale. Large codebases have thousands of tests, tagged by subsystem, with tiering (smoke tests run on every commit, full suite runs nightly). Eval suite management applies the same discipline.

## Stage 2: The Execution Engine

Running evals at scale is an infrastructure challenge. Each eval case may require:
- A fresh sandbox with a specific codebase and toolchain
- Multiple LLM calls (the agent may take 5-30 turns)
- Tool execution (file operations, test runs, builds)
- Minutes of wall-clock time

### Parallelism

Running 500 eval cases sequentially at 5 minutes each takes 42 hours. Running them on 50 parallel workers takes 50 minutes. The execution engine must:
- Manage a pool of sandbox workers (Adaptive Sandbox Fan-Out Controller, Module 16)
- Queue and schedule eval cases across workers
- Handle failures gracefully (worker crash → reschedule the case)
- Collect results from all workers into a unified store

### Determinism and Reproducibility

Agent behavior is nondeterministic (Module 1). The same eval case might pass 4 out of 5 runs. The execution engine must:
- Run each case multiple times (typically 3-5) to estimate pass rate
- Use temperature 0 where possible to reduce variance
- Record the full trajectory (every message, tool call, tool result) for debugging
- Enable replay: re-run a specific case with the exact same context to reproduce a failure

### Pattern: AI Web Search Agent Loop

**What it does**: An agent that searches the web, evaluates results, follows links, and synthesizes information — operating as an autonomous research agent that iterates until it finds what it needs.

**SE parallel**: Web crawler architecture (Googlebot, Scrapy). A crawler starts with seed URLs, fetches pages, extracts links, decides which to follow, and aggregates content. The AI Web Search Agent Loop applies this to research tasks: start with a query, evaluate results, decide which links to explore deeper, and synthesize findings.

**How it works**:
```
1. Generate search queries from the research question
2. Execute searches (web search API)
3. Evaluate results for relevance
4. For promising results, fetch the full page
5. Extract relevant information
6. Decide: enough information to answer? If not, generate refined queries
7. Synthesize findings into a structured answer
```

**Where it fits in eval infrastructure**: The AI Web Search Agent Loop is one of the hardest capabilities to evaluate — the agent's search strategy, result evaluation, and synthesis are all judgment calls with no single correct answer. Evaluating it requires rubric-based grading (not exact-match), makes it a representative example of the hardest eval challenges.

**Trade-off**: Web search results change over time, making evals non-deterministic even with temperature 0. The eval must account for this — evaluating the search strategy and synthesis quality rather than the specific facts retrieved.

## Stage 3: The Grading System

How do you determine whether an eval case passed? This is the hardest stage.

### Grading Approaches

**Exact match**: The output must match a specific expected output. Works for structured tasks (JSON output, classification). Fails for generative tasks (code, explanations).

**Test-based**: The output is tested by running code. "Does the generated function pass this test suite?" Objective and reliable, but only applicable to code-generating agents.

**Rule-based**: Heuristic checks. "Does the output contain an SQL injection vulnerability?" "Is the output under 500 tokens?" "Does the code compile?" Fast, deterministic, and composable — but limited to surface-level quality.

**LLM-as-judge**: A separate model grades the output against a rubric (RLAIF, Module 14). Handles nuanced quality assessment but is itself nondeterministic and biased. Must be calibrated against human judgments.

**Human evaluation**: The gold standard for quality, but expensive and slow. Used to: calibrate LLM judges, review disagreements, and evaluate novel capabilities.

### Grader Design Principles

From Anti-Reward-Hacking Grader Design (Module 14):

1. **Grade properties, not specifics**: "Does the code handle all error cases?" not "Does the code match this expected implementation?"
2. **Use multiple grading signals**: Combine test-based (objective) + rule-based (surface quality) + LLM-judge (deep quality). Agreement across signals increases confidence.
3. **Calibrate against humans**: Regularly compare LLM-judge grades against human expert grades. Track correlation. If the LLM judge disagrees with humans more than 20% of the time, recalibrate the rubric.
4. **Version the rubric**: When grading criteria change, version the change. Results graded under rubric v1 are not directly comparable to results graded under rubric v2.

## Stage 4: Reporting and Gating

### Dashboards

The eval infrastructure produces data. Dashboards make it actionable:

- **Headline metrics**: Overall pass rate, pass rate by category, cost per eval case
- **Trend analysis**: How are metrics changing over time? Is the agent getting better or worse?
- **Comparison views**: Side-by-side comparison of two prompt versions, two models, or two configurations
- **Failure analysis**: For failed cases, what went wrong? Common failure categories, example trajectories

### Deploy Gates

Eval results gate deployments (Canary Rollout, Module 14):
- **Block gate**: New configuration cannot deploy if eval pass rate drops by more than X% vs. baseline
- **Warning gate**: Alert but allow deployment if the drop is between Y% and X%
- **Auto-promote**: If eval pass rate improves or stays within threshold, automatically promote to wider deployment

**SE parallel**: CI quality gates. A build that drops test coverage below 80% is blocked. A build that introduces a security vulnerability is blocked. Eval gates do the same for agent quality — prompt changes that regress eval scores don't ship.

### The Flywheel

The complete system forms a flywheel:

```
Better evals → Better quality measurement
→ Better deployment decisions → Fewer production incidents
→ Incidents become new eval cases (Incident-to-Eval Synthesis)
→ Better evals → ...
```

Each cycle makes the system stronger. After a year of operation, you have thousands of eval cases covering real failure modes, rubrics calibrated against human judgment, graders that are more accurate than any individual reviewer, and deployment gates that prevent the regressions that used to ship to production.

This flywheel is the Compounding Engineering Pattern (Module 13) applied to quality infrastructure. It's why eval infrastructure is the moat — it compounds, and compounds are very hard to replicate.

## Key Takeaways

1. Eval infrastructure is the single most important investment in an agent platform — it enables data-driven quality management for models, prompts, tools, and configurations.
2. The eval pipeline has four stages: case management (design, version, sample), execution (parallel sandboxed runs), grading (test + rule + LLM-judge + human), and reporting/gating (dashboards and deploy gates).
3. At scale, eval suites need strategic sampling — always run regressions, stratified-sample the rest, target-run for specific changes.
4. Graders must resist gaming: grade properties not specifics, combine multiple signals, and calibrate against human judgment.
5. The eval flywheel (evals → quality → fewer incidents → more evals) is the Compounding Engineering Pattern applied to quality. It's the moat.

## Try This

Build a minimal eval pipeline:
1. Define 10 eval cases for a coding agent: 3 unit (mocked tools), 3 integration (real tool execution), 2 regression (from real failures), 2 adversarial (prompt injection, scope creep).
2. Implement automated grading: use test execution (does the code pass?) + rule checks (does it compile? under token budget?) + an LLM judge (quality rubric scored 1-5).
3. Run all 10 cases against the current agent configuration. Record pass rates.
4. Make a prompt change. Re-run. Compare.
5. Decide: would you deploy the prompt change based on the eval results?

This gives you hands-on experience with the entire pipeline — case design, execution, grading, and decision-making.

## System Design Question

You're designing the eval infrastructure for a platform with 50 agent configurations (different teams, different use cases) and 5,000 total eval cases. Eval cases take an average of 3 minutes to run. Design the system: How do you schedule eval runs (on every prompt change? nightly? on-demand)? How do you manage the compute budget for 5,000 × 3-minute runs? How do you handle eval cases that are nondeterministic (pass 3 of 5 times)? How do you enable team-specific eval suites while maintaining platform-wide quality baselines? What's your strategy for migrating to a new model version — how do you evaluate it across all 50 configurations before deploying?
