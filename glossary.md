# Glossary

Consistent terminology definitions used throughout the course. Updated as each module is written.

---

**Autoregressive generation** — The process by which an LLM generates output one token at a time, where each new token depends on all previous tokens. *(First introduced: Module 1)*

**LLM (Large Language Model)** — A neural network with billions of learned parameters (weights) that takes a sequence of tokens as input and returns a probability distribution over the next token. The computational primitive underlying all agent systems. *(First introduced: Module 1)*

**Context window** — The fixed maximum number of tokens an LLM can process in a single call, including both input and output. The model's effective RAM. *(First introduced: Module 1)*

**Contextual knowledge** — Information provided directly in the prompt. Fresh and accurate but limited by context window size. *(First introduced: Module 1)*

**Inference** — The process of running a trained model to produce output from input. Querying the model. *(First introduced: Module 1)*

**Multimodal** — A model capable of processing multiple input types (text, images, audio) rather than text only. Relevant for agents that interpret screenshots, diagrams, or visual output. *(First introduced: Module 1)*

**Knowledge cutoff** — The date beyond which a model has no training data. Parametric knowledge is frozen at this point. *(First introduced: Module 1)*

**Parametric knowledge** — Facts encoded in a model's weights during training. Broad but potentially outdated or incorrect. *(First introduced: Module 1)*

**Retrieved knowledge** — Information fetched by tools at runtime and injected into the context. The basis of RAG. *(First introduced: Module 1)*

**Sampling** — The strategy used to select a token from the model's probability distribution. Controlled by temperature, top-p, and top-k parameters. *(First introduced: Module 1)*

**Self-attention** — The transformer mechanism where each token computes relevance scores against every other token. O(n^2) in sequence length. *(First introduced: Module 1)*

**Self-supervised learning** — Training approach where the data provides its own labels — for LLMs, the next token in a sequence serves as the training target. *(First introduced: Module 1)*

**Temperature** — Sampling parameter controlling randomness. 0 = deterministic (always pick highest probability), higher values = more random. *(First introduced: Module 1)*

**Transformer** — The neural network architecture underlying all modern LLMs. Key mechanism is self-attention, which computes relevance between all token pairs at O(n^2) cost. *(First introduced: Module 1)*

**Token** — The atomic unit of an LLM's vocabulary. A subword chunk determined by the tokenizer. The unit of billing, context measurement, and processing. *(First introduced: Module 1)*

**Top-k** — Sampling strategy that considers only the k most probable next tokens. *(First introduced: Module 1)*

**Top-p (nucleus sampling)** — Sampling strategy that considers the smallest set of tokens whose cumulative probability exceeds threshold p. *(First introduced: Module 1)*

**Batch API** — Provider endpoint for non-latency-sensitive requests, typically offered at ~50% discount. *(First introduced: Module 2)*

**Decode (generation phase)** — The second phase of inference where output tokens are generated one at a time, sequentially. Memory-bandwidth-bound. More expensive per token than prefill. *(First introduced: Module 2)*

**Extended thinking (reasoning tokens)** — Internal chain-of-thought tokens generated before the visible response. Billed as output tokens. Improves quality on complex tasks at higher cost. *(First introduced: Module 2)*

**KV cache** — Cached key-value pairs from the attention mechanism, stored during prefill so they don't need recomputation during decode. *(First introduced: Module 2)*

**Prefill (input processing phase)** — The first phase of inference where all input tokens are processed in parallel. Compute-bound. *(First introduced: Module 2)*

**Prompt caching** — Provider optimization that reuses KV cache when a request's byte prefix matches a recent request. Typically 90% discount on cached input tokens. *(First introduced: Module 2)*

**Time to first token (TTFT)** — Latency before the first output token appears. Dominated by prefill time; increases with prompt length. *(First introduced: Module 2)*

**Tokens per second (TPS)** — Output generation speed. Typically 30-100 TPS for frontier models via API. *(First introduced: Module 2)*

**Chain-of-thought prompting** — Technique of asking the model to reason step by step before producing a final answer. Trades output tokens for improved accuracy. *(First introduced: Module 3)*

**Constrained decoding** — Enforcing output structure at the token-generation level, guaranteeing valid output matching a schema. *(First introduced: Module 3)*

**Evals (evaluations)** — Test suites for LLM outputs. Run prompts against known inputs and measure output quality statistically, since LLM outputs are nondeterministic. *(First introduced: Module 3)*

**Few-shot prompting** — Including input/output examples in the prompt to steer model behavior. Functions as both specification and test cases. *(First introduced: Module 3)*

**Prompt composition** — Assembling a prompt from independent components (system rules, tool definitions, context, history) rather than writing monolithic prompts. *(First introduced: Module 3)*

**Structured output** — Constraining the model's response to match a specific schema (e.g., JSON). Eliminates parsing errors and enables reliable automation. *(First introduced: Module 3)*

**System prompt** — The highest-authority instruction block in an API call, defining the model's persona, constraints, output format, and behavioral rules. Analogous to main() or bootstrap configuration. *(First introduced: Module 3)*

**Agent** — A system where an LLM makes decisions about control flow — choosing which tool to call, whether to continue, and what to investigate next. Distinguished from workflows (predetermined steps) and pipelines (fixed sequences). *(First introduced: Module 4)*

**Agent loop** — The core execution cycle: compose context, call LLM, parse response, execute tool or return result, check stop conditions, repeat. *(First introduced: Module 4)*

**Stop condition** — A rule that terminates the agent loop — token budget, turn limit, error threshold, time limit, or task completion. Prevents runaway execution. *(First introduced: Module 4)*

**Tool** — A function available to an agent, defined by a name, natural-language description, parameter schema (JSON Schema), and implementation. The unit of agent capability. *(First introduced: Module 4)*

**Tool registry** — The collection of all tools available to an agent, including their descriptions and schemas. Analogous to a service registry with API documentation. *(First introduced: Module 4)*

**Graph of Thoughts (GoT)** — Reasoning pattern that extends ToT by allowing branches to merge into a DAG, combining insights from independent reasoning paths. *(First introduced: Module 5)*

**Inference-Time Scaling** — Dynamically adjusting reasoning compute based on task difficulty — cheap inference for easy tasks, extended thinking or tree search for hard ones. *(First introduced: Module 5)*

**LATS (Language Agent Tree Search)** — Monte Carlo Tree Search applied to LLM reasoning. Explores, simulates, and backpropagates value to focus search on promising branches. *(First introduced: Module 5)*

**Plan-Then-Execute** — Reasoning pattern that separates planning (generate a step list) from execution (carry out steps), enabling cheaper models for the execution phase. *(First introduced: Module 5)*

**ReAct (Reason + Act)** — Agent reasoning pattern that alternates explicit thinking and tool use. The default pattern for most agent implementations. *(First introduced: Module 5)*

**Self-Discover** — Reasoning pattern where the LLM selects and composes reasoning strategies from a library before solving a problem, analogous to runtime query plan optimization. *(First introduced: Module 5)*

**Tree-of-Thought (ToT)** — Reasoning pattern that explores multiple reasoning paths in parallel, evaluates each, prunes weak ones, and continues the most promising. *(First introduced: Module 5)*

**CodeAct Agent** — Pattern where the agent writes and executes code as its primary action language instead of using predefined tool calls. Maximally flexible but requires strong sandboxing. *(First introduced: Module 6)*

**MCP (Model Context Protocol)** — A standard protocol for connecting agents to external tool servers via typed interfaces. The tool equivalent of gRPC/protobuf for service interoperability. *(First introduced: Module 6)*

**Vector embeddings** — Dense numerical representations of text (or other content) in a high-dimensional space, where semantic similarity maps to geometric proximity. The basis of semantic search. *(First introduced: Module 6)*

**Archive memory** — The lowest tier of agent memory. Persists across sessions in filesystem or database. Large capacity, high retrieval latency. Contains session summaries, user preferences, project knowledge. *(First introduced: Module 7)*

**Auto-compaction** — Automatic summarization or truncation of older conversation history when context approaches its limit. Lossy compression that trades fidelity for space. *(First introduced: Module 7)*

**Episodic memory** — Storage and retrieval of specific past experiences (tool invocations, decisions, outcomes) rather than general knowledge. Used to learn from past agent behavior. *(First introduced: Module 7)*

**Main memory (session-scoped)** — The middle tier of agent memory. Stores information compacted out of the context window but still available within the current session via retrieval. *(First introduced: Module 7)*

**RAG (Retrieval-Augmented Generation)** — Pattern that supplements model parametric knowledge with information retrieved from an external knowledge store at query time. Bridges the knowledge cutoff. *(First introduced: Module 7)*

**Working memory** — The top tier of agent memory, equivalent to the current context window. Small, expensive, always visible to the model. Contains current conversation, recent tool results, active task state. *(First introduced: Module 7)*

**Multi-agent architecture** — System design using multiple LLM agents with specialized roles, different models, or different contexts, coordinated to complete tasks that exceed a single agent's capabilities. *(First introduced: Module 8)*

**Router agent** — A lightweight agent or heuristic that classifies incoming tasks and routes them to the appropriate model or specialized agent. Analogous to a reverse proxy or intelligent load balancer. *(First introduced: Module 8)*

**Orchestrator-Worker** — Multi-agent topology where a single orchestrator decomposes tasks, assigns them to worker agents, and synthesizes results. Analogous to master-worker in distributed computing. *(First introduced: Module 9)*

**Sub-agent** — A child agent dynamically spawned by a parent agent to handle a subtask, with its own fresh context window. Analogous to fork/exec. *(First introduced: Module 9)*

**State machine (agent)** — Explicit modeling of an agent's execution as defined states with valid transitions, enabling recovery from failures and predictable behavior. *(First introduced: Module 11)*

**Eval suite** — A growing collection of test cases (input, expected output) used to evaluate agent quality. Derived from synthetic cases and real production incidents. *(First introduced: Module 12)*

**Feedback loop (agent)** — A closed-loop mechanism where an agent's output is evaluated and the evaluation drives corrective action — either within the same session (reflection) or across sessions (reward shaping). *(First introduced: Module 12)*

**Reflection loop** — Agent self-evaluation cycle: generate, review, revise. The agent critiques its own output before presenting the final result. *(First introduced: Module 12)*

**Reward signal** — An observable outcome (test pass/fail, review approval, user satisfaction) used to shape future agent behavior through prompt tuning or model training. *(First introduced: Module 12)*

**Agent RFT (Reinforcement Fine-Tuning)** — Fine-tuning a model on successful agent trajectories so it learns to reproduce effective reasoning, tool use, and decision patterns. *(First introduced: Module 13)*

**Fine-tuning** — Additional training of a pre-trained model on a smaller, domain-specific dataset to improve performance on specific tasks. Modifies model weights. *(First introduced: Module 13)*

**Skill library** — A growing collection of reusable agent capabilities (prompt templates, tool chains, workflows) extracted from successful task completions. The agent equivalent of a package registry. *(First introduced: Module 13)*

**Canary rollout** — Deploying agent changes to a small percentage of traffic first, monitoring quality metrics, and automatically rolling back if quality degrades. *(First introduced: Module 14)*

**Constitution (agent)** — A versioned, auditable set of behavioral rules governing what an agent can and cannot do. Injected into the system prompt and enforced by the runtime. *(First introduced: Module 14)*

**Egress lockdown** — Restricting an agent's outbound network access to an explicit allow-list of endpoints. Prevents data exfiltration regardless of agent behavior. *(First introduced: Module 15)*

**Lethal Trifecta** — The three capabilities that create catastrophic risk when combined: real-world actions + sensitive data access + unsupervised autonomy. The organizing framework for agent security. *(First introduced: Module 15)*

**Prompt injection** — Attack where malicious content in user input or retrieved documents tricks the agent into unauthorized actions. The primary novel attack surface for agent systems. *(First introduced: Module 15)*

**RLAIF (Reinforcement Learning from AI Feedback)** — Using one model to evaluate another model's output at scale, generating automated quality labels for training or prompt refinement. *(First introduced: Module 14)*

**Sandbox** — An isolated execution environment (container, VM) with restricted permissions, filesystem, network, and resources. The primary containment mechanism for agent-executed code. *(First introduced: Module 15)*

**Agent runtime** — The execution environment that manages an agent's lifecycle: session management, prompt composition, tool execution, sandbox orchestration, and model abstraction. Analogous to an application server (Tomcat, Express). *(First introduced: Module 17)*

**Deploy gate** — An automated quality check that blocks deployment of agent changes (prompts, models, tools) if eval metrics regress beyond a defined threshold. *(First introduced: Module 19)*

**Eval pipeline** — End-to-end infrastructure for agent evaluation: case management, parallel execution, automated grading, and reporting with deployment gates. The CI/CD equivalent for agent quality. *(First introduced: Module 19)*

**LLM-as-judge** — Using a separate model to grade another model's output against a rubric. Enables automated quality assessment at scale but requires calibration against human judgment. *(First introduced: Module 19)*

**Platform (agent)** — Infrastructure that enables other developers to build, configure, deploy, and operate agents: runtime + platform services + extension points + developer experience. Distinguished from a single agent product. *(First introduced: Module 18)*

**Webhook trigger** — An external event (GitHub push, Jira ticket, cron schedule) that activates an agent session through an event ingestion system. Enables event-driven agent automation. *(First introduced: Module 18)*

**Human-in-the-loop** — Interaction pattern where the agent proposes actions and a human approves, rejects, or redirects before execution. Risk-tiered: low-risk auto-approves, high-risk requires explicit approval. *(First introduced: Module 20)*

**Spectrum of Control** — A continuum of agent autonomy levels from fully manual (agent suggests only) to fully autonomous, adjustable per task and per action type. Analogous to self-driving L0-L5. *(First introduced: Module 20)*

**Weights (parameters)** — The learned numerical values in a neural network that encode the model's knowledge. A model's "storage format." *(First introduced: Module 1)*

**Zero-shot prompting** — Giving the model a task with no examples, relying entirely on parametric knowledge. *(First introduced: Module 3)*
