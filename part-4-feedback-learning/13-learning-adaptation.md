# Module 13: Learning & Adaptation

**Software engineering parallel**: Continuous delivery and platform evolution — the mechanisms that turn raw feedback into systematic improvement: deployment pipelines, A/B testing, package registries, and the organizational patterns that compound engineering velocity over time.

**Patterns covered**: Self-Improving Agent via Feedback Signals, Iterative Prompt & Skill Refinement, Dogfooding with Rapid Iteration, Agent Reinforcement Fine-Tuning (Agent RFT), Skill Library Evolution, Memory Reinforcement Learning (MemRL), Variance-Based RL Sample Selection, Compounding Engineering Pattern, Frontier-Focused Development, Shipping as Research

---

## From Feedback to Learning

Module 12 covered how agents receive feedback — reflection, CI results, review signals, incident-to-eval pipelines. This module covers what happens *after* the feedback arrives: how it's converted into durable improvement that compounds over time.

The distinction matters. A feedback loop that catches a bug in the current session is valuable. A learning system that ensures the agent never makes that type of bug again is transformative. Module 12 is the sensor; Module 13 is the actuator.

## Group 1: Prompt-Level Learning

These patterns improve agent behavior by modifying prompts, examples, and configuration — without retraining model weights.

### Self-Improving Agent via Feedback Signals

**What it does**: Automatically adjusts the agent's system prompt, few-shot examples, or tool-use guidance based on aggregated feedback signals (eval results, user satisfaction, task success rate).

**SE parallel**: A/B testing → deploy winner. Run two variants of your service, measure which performs better, deploy the winner. Self-improving agents do the same with prompts: test variant A vs. B on the eval suite, deploy the one with better scores.

**How it works**:
1. Collect feedback signals across sessions (eval pass rate, user acceptance rate, tool-use efficiency)
2. Identify underperforming areas ("code review comments about error handling are rejected 40% of the time")
3. Generate prompt modifications ("add instruction: always include error handling for network calls")
4. Test the modification against the eval suite (Module 12's Incident-to-Eval)
5. If improvement is statistically significant, deploy. If regression, discard.

**Trade-off**: Automated prompt modification can introduce subtle regressions. A change that improves error handling might degrade performance on unrelated tasks. The eval suite must have broad coverage, and changes should be deployed incrementally (Swarm Migration, Module 10).

### Iterative Prompt & Skill Refinement

**What it does**: Treats prompt engineering as a continuous deployment pipeline — prompts are versioned, tested, deployed, monitored, and refined in ongoing cycles.

**SE parallel**: Continuous deployment. You don't write code, deploy once, and walk away. You deploy, monitor, gather feedback, improve, deploy again. Iterative refinement applies the same cadence to prompts: version 1 ships, eval results come in, version 1.1 addresses weaknesses, eval results improve, version 1.2 ships.

**How it works**: Maintain a prompt changelog alongside the eval suite. Every prompt change is:
- Versioned (git-tracked)
- Tested against the full eval suite before deployment
- Monitored in production for regression
- Rolled back if quality drops

**Why it matters**: Prompts are the most impactful lever for agent quality. A 5% improvement in prompt quality — measured by eval pass rate — can save thousands of dollars in wasted sessions and failed tasks. But prompt improvement without systematic testing is guesswork.

### Dogfooding with Rapid Iteration

**What it does**: Uses the agent internally (dogfooding) with fast iteration cycles to discover failure modes before users encounter them.

**SE parallel**: Internal beta programs / eating your own dogfood. Google uses Gmail internally before public release. Microsoft uses Windows daily. Dogfooding surfaces usability issues and edge cases that synthetic testing misses.

**Applied to agents**: Before deploying a prompt change or new capability to users, deploy it to the development team. Developers use the agent for real work, encounter real edge cases, and report failures. Each failure feeds into the eval suite (Incident-to-Eval Synthesis, Module 12) and drives prompt refinement.

**Why rapid?** The feedback cycle must be short — hours, not weeks. If a dogfooding failure takes two weeks to reach the prompt engineer, the iteration speed is too slow. The ideal loop: developer encounters failure → failure is logged → eval case is generated → prompt is modified → fix is tested → deployed to dogfood within 24 hours.

## Group 2: Model-Level Learning

These patterns go beyond prompt modification to improve the model itself — through fine-tuning, reinforcement learning, or training data curation.

### Agent Reinforcement Fine-Tuning (Agent RFT)

**What it does**: Fine-tunes the base model on successful agent trajectories — the sequences of reasoning, tool use, and decisions that led to good outcomes. The model learns to reproduce effective agent behavior.

**SE parallel**: Retraining pipelines. Production ML systems continuously retrain on new data to stay accurate as the world changes. Agent RFT retrains the model on new agent trajectories to improve the behaviors that matter — tool selection, reasoning quality, error recovery.

**How it works**:
1. Collect successful agent trajectories (complete sessions where the task was completed correctly)
2. Filter for quality (sessions with human approval, passing tests, positive feedback)
3. Fine-tune the model on these trajectories as training examples
4. Evaluate the fine-tuned model against the eval suite
5. Deploy if improvement is confirmed; retain the base model as fallback

**When to use it**: When you have access to a model you can fine-tune (open-source or via provider fine-tuning APIs), and you have hundreds to thousands of high-quality trajectories. Not applicable to closed-source API models you can't fine-tune.

**Trade-off**: Fine-tuning is expensive and risks catastrophic forgetting — improving agent behavior on coding tasks might degrade general-purpose capabilities. Requires careful evaluation across diverse tasks, not just the domain you fine-tuned on.

### Memory Reinforcement Learning (MemRL)

**What it does**: Uses reinforcement learning signals to optimize what the agent stores in and retrieves from memory. The memory system learns which information is worth keeping and which can be discarded.

**SE parallel**: Adaptive caching. Traditional caches use fixed policies (LRU, LFU). Adaptive caches learn from access patterns: "this key is accessed every Tuesday at 9am — pre-warm it." MemRL applies the same principle: "this type of context is retrieved frequently and improves task success — prioritize storing it."

**How it works**: Track which memory retrievals correlate with task success. If retrieving "project configuration" at session start leads to 30% fewer errors, the memory system learns to always inject project configuration. If retrieving "last session's conversation summary" rarely helps, the system learns to skip it.

**Trade-off**: Requires substantial data to learn meaningful patterns. Early-stage systems should use hand-tuned memory policies; MemRL is an optimization for mature systems with enough data to learn from.

### Variance-Based RL Sample Selection

**What it does**: Selects training examples for reinforcement learning based on variance — focusing on examples where the model's performance is most inconsistent, which is where learning has the highest marginal value.

**SE parallel**: Stratified sampling / focus testing on flaky areas. If a test is flaky (sometimes passes, sometimes fails), that's where you should invest debugging effort. Variance-Based Selection applies the same logic: if the model sometimes succeeds and sometimes fails on a task type, that's where fine-tuning data has the most impact.

**How it works**: Run each eval case multiple times (e.g., 5 runs). Calculate the variance in outcomes. High variance = the model "knows" the task but is unreliable → this is the best training target. Low variance + high success = the model has already learned this → skip. Low variance + low success = the model fundamentally can't do this → skip (or escalate to a more capable model).

**When to use it**: When curating training data for Agent RFT or selecting which eval cases to prioritize for prompt tuning. The insight is that not all training data is equally valuable — variance-based selection maximizes the information per training example.

### Skill Library Evolution

**What it does**: The agent accumulates reusable skills (prompt templates, tool chains, workflows) in a library that grows over time. New tasks check the library first before building from scratch.

**SE parallel**: npm / package registry. Instead of reimplementing string manipulation functions in every project, you install a package. Skill Library Evolution creates the same ecosystem for agent capabilities: solved problems become reusable skills.

**How it works**: When an agent completes a task type successfully, the effective approach (prompt + tool sequence + validation criteria) is extracted and stored as a named skill. When a future task matches the skill's description, the skill is loaded as a template rather than reasoning from first principles.

**Example**: The agent successfully implements OAuth2 integration. The skill — including the implementation steps, common pitfalls, and test patterns — is saved as "oauth2-integration." When another project needs OAuth2, the skill is loaded, reducing the task from a 30-step exploration to a 10-step template execution.

**Trade-off**: Skills can become stale as libraries, APIs, and best practices evolve. The library needs a maintenance process — version skills, track usage, deprecate outdated ones. Same as maintaining any package registry.

## Group 3: Meta-Patterns for Agent Evolution

These patterns are not technical mechanisms but engineering strategies for building agent systems that improve faster than the competition.

### Compounding Engineering Pattern

**What it does**: Structures engineering investments so that each improvement makes future improvements easier — creating compounding returns rather than linear ones.

**SE parallel**: Compound interest in tech debt payoff. Every piece of tech debt you pay off makes future changes cheaper. Every test you add makes future regressions cheaper to catch. Compounding Engineering applies this to the entire agent stack.

**Concrete example**: Invest in eval infrastructure first. Eval infrastructure makes prompt improvements measurable. Measurable prompt improvements make feedback loops tighter. Tighter feedback loops make skill library curation faster. Faster curation makes the agent better, which generates more usage data, which improves evals. Each investment amplifies the returns of every other investment.

**The anti-pattern**: Investing in flashy features (new tools, new models, new UI) without building the feedback and evaluation infrastructure that makes those features reliably good. Features without evals are tech demos; features with evals are products.

### Frontier-Focused Development

**What it does**: Designs the agent system architecture for the *next* generation of models, not just the current one — so that when a more capable model drops, you can immediately exploit its capabilities.

**SE parallel**: Building for next-gen hardware. Game engines are designed for future GPUs, not current ones. API architectures are designed for future usage patterns. Frontier-focused development designs the agent infrastructure for future model capabilities.

**Concrete example**: Today's models occasionally fail at complex multi-file refactoring. Instead of designing around that limitation (e.g., only allowing single-file edits), design the orchestration system to support multi-file refactoring and add guardrails for current models. When the next model generation succeeds at multi-file refactoring, you remove the guardrails instead of rebuilding the orchestration.

**Why it matters**: Model capability is improving rapidly. Architecture that was designed around today's limitations becomes technical debt when those limitations are lifted. Design for where the capability is heading, not where it is today.

### Shipping as Research

**What it does**: Treats production deployment as the primary research methodology — learning what works by shipping it and measuring, rather than theorizing or benchmarking in isolation.

**SE parallel**: Lean startup / build-measure-learn. Instead of spending months in the lab perfecting a feature, ship an MVP, measure real-world outcomes, and iterate based on data. The production environment surfaces realities that no benchmark can capture.

**Applied to agents**: Instead of running benchmarks to decide if a new reasoning strategy works, deploy it to a small percentage of traffic (canary, Module 10's Swarm Migration), measure real outcomes (task success rate, user satisfaction, cost per task), and make data-driven decisions. A strategy that scores 5% worse on benchmarks but 10% better in production is the one you should ship.

**Trade-off**: Requires robust monitoring, canary infrastructure, and fast rollback capability. You can't "ship as research" if you can't detect and revert failures quickly. This is only possible once the feedback infrastructure from Module 12 is mature.

## Key Takeaways

1. Self-Improving Agent via Feedback Signals automates the prompt improvement cycle: collect signals, identify weaknesses, generate modifications, test, deploy. The eval suite (Module 12) is the gatekeeper.
2. Agent RFT fine-tunes the model on successful trajectories — the most powerful learning mechanism but requires fine-tuning access and risks catastrophic forgetting.
3. Skill Library Evolution turns solved problems into reusable templates, reducing future costs. The agent equivalent of a package registry.
4. Compounding Engineering invests in eval infrastructure and feedback loops first — these amplify the returns of every other improvement.
5. Frontier-Focused Development designs for future model capabilities so you can exploit improvements immediately rather than rebuilding.

## Try This

Build a simple skill library:
1. Have an agent complete 5 similar tasks (e.g., "add input validation to a REST endpoint" across different codebases).
2. After each successful completion, extract the approach: what files were read, what patterns were applied, what tests were written.
3. Synthesize a reusable skill template: a prompt that captures the generalizable approach.
4. Give the agent the 6th task with the skill template pre-loaded. Compare: does it complete faster? With fewer errors? At lower cost?

This exercise demonstrates how accumulated experience becomes reusable knowledge — the core mechanism behind Skill Library Evolution.

## System Design Question

You're designing the learning infrastructure for an agent platform that serves 1,000 developers. The agents collectively process 10,000 tasks per day. Design the learning pipeline: How do you collect training signal from those 10,000 tasks? How do you select which signals to learn from (Variance-Based Selection)? How do you test improvements safely (Swarm Migration)? How do you measure whether the platform is actually getting better month-over-month? What's the feedback latency from "incident occurs" to "agent is improved" and how would you reduce it?
