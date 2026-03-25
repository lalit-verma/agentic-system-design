# Module 1: What LLMs Actually Are

**Software engineering parallel**: A database engine — it has a storage format (weights), a query language (prompts), a query planner (attention mechanism), and returns results that depend entirely on how you ask.

**Patterns covered**: None (foundational module — establishes the mental model that all later patterns build on)

---

## The One-Sentence Version

A large language model (LLM) is a stateless function that takes a sequence of text (called tokens) and returns a probability distribution over what token comes next. Everything else — chatbots, code generation, reasoning, agents — is built on top of this single primitive.

If that sounds underwhelming, good. The gap between "predict the next token" and "autonomously write and ship code" is where every pattern in this course lives.

## From Text Prediction to Useful Computation

### The Training Phase: Building the Index

Think of LLM training as building a massive, lossy index over human knowledge — similar to how a search engine crawls the web and builds an inverted index, except the "index" here is a neural network with billions of learned parameters (called weights).

During training, the model reads enormous volumes of text — books, code repositories, documentation, conversations — and adjusts its weights to become better at predicting what comes next in a sequence. This is called **self-supervised learning**: the training data provides its own labels, because the "right answer" for any prefix of text is simply the token that actually followed it.

The result is not a lookup table. The model doesn't store documents verbatim (usually). Instead, it compresses patterns, relationships, and structures into a dense mathematical representation. When you later query the model, it reconstructs plausible continuations based on these compressed patterns.

**SE parallel**: This is analogous to how a B-tree index doesn't store your rows — it stores a compressed structure that lets you find rows efficiently. The index is far smaller than the raw data, but it captures the access patterns you need. An LLM's weights are a "statistical index" over language patterns, far smaller than the training corpus, but encoding enough structure to generate useful outputs.

### The Inference Phase: Querying the Engine

When you send a prompt to an LLM, you're running a query against this statistical index. The model processes your input and produces output one token at a time, left to right. Each token generation is a separate forward pass through the network — the model looks at everything so far (your prompt plus any tokens it has already generated) and picks the next token.

This is called **autoregressive generation**: each output depends on all previous outputs. It's sequential by nature, which has deep implications for latency and cost that we'll cover in Module 2.

**SE parallel**: Think of it as a streaming response where each chunk depends on the previous chunks — like a server that generates each line of a log file based on the lines it has already written. You can't parallelize the output generation itself, though you can parallelize across independent requests (like handling multiple HTTP connections concurrently).

### What "Tokens" Actually Are

Tokens are the atomic units of an LLM's vocabulary. They are not words. They are not characters. They're subword chunks determined by a tokenizer algorithm (typically Byte Pair Encoding or similar). Common words like "the" are single tokens. Uncommon words get split: "tokenization" might become ["token", "ization"]. Code has its own patterns: common keywords are single tokens, but unusual variable names get fragmented.

Why does this matter for system design?

1. **You're billed per token** — both input and output. Understanding tokenization is understanding your cost model.
2. **Context windows are measured in tokens** — not words, not characters. A 200K-token context window holds roughly 150K words, but the ratio varies by language and content type.
3. **Tokenization affects quality** — models reason better about concepts that map cleanly to single tokens than about concepts that get fragmented across multiple tokens. This will matter when we discuss tool design in Module 6.

## The Context Window: Your Working Memory Budget

Every LLM has a fixed-size **context window** — the maximum number of tokens it can consider at once. This includes both your input (the prompt) and the model's output (the completion). As of early 2026, context windows range from 8K tokens (small open-source models) to 1M+ tokens (frontier models like Claude).

**SE parallel**: The context window is the LLM equivalent of RAM. Your process can only work with data that fits in memory. Need more? You have to decide what to page in and what to evict — exactly the problem that buffer pool management solves in databases. This constraint drives many of the memory and context patterns in Part 2.

A critical property: **LLMs are stateless between calls**. Each API call is independent. The model has no memory of previous interactions unless you explicitly include prior conversation history in the current prompt. Every turn of a conversation, you're re-sending the entire conversation so far.

**SE parallel**: This is like a REST API taken to the extreme — not just stateless in the "no server-side session" sense, but stateless in the "I literally forget you exist between requests" sense. All state management is pushed to the caller. This is why agent frameworks exist: they manage the state that the model cannot.

## Temperature and Sampling: Controlling Nondeterminism

When the model produces a probability distribution over next tokens, you need a strategy to pick one. This is the **sampling** step, and it's controlled by several parameters:

- **Temperature** (0.0 to 2.0): Controls randomness. At 0, the model always picks the highest-probability token (deterministic, like a cache hit). At 1.0+, it samples more broadly from the distribution (stochastic, like shuffling results).
- **Top-p (nucleus sampling)**: Instead of considering all possible tokens, only consider the smallest set whose cumulative probability exceeds p. Top-p of 0.9 means "consider tokens until you've covered 90% of the probability mass, ignore the long tail."
- **Top-k**: Only consider the k most probable tokens.

**SE parallel**: This is load balancer selection strategy. Round-robin (deterministic) vs. weighted random (stochastic) vs. "pick from top N healthy servers" (top-k). Different tasks need different strategies: you want deterministic output for structured data extraction (temperature 0), but stochastic output for creative brainstorming (temperature 0.7+).

For agentic systems, you'll typically want low temperature (0-0.3) for tool calls and structured actions, and moderate temperature (0.5-0.7) for planning and reasoning. This duality — precision for execution, creativity for strategy — is a recurring theme.

## What the Model Actually "Knows"

LLMs have a **knowledge cutoff** — a date beyond which they have no training data. They cannot access the internet, query databases, or read files unless you give them tools to do so (Module 6). Everything the model "knows" is baked into its weights at training time.

This creates three categories of knowledge:

1. **Parametric knowledge** — facts encoded in the model's weights during training. Broad but can be outdated or wrong. Like a snapshot of a database: accurate as of the snapshot date, increasingly stale afterward.
2. **Contextual knowledge** — information you provide in the prompt. Fresh and accurate, but limited by the context window. Like passing query parameters.
3. **Retrieved knowledge** — information fetched by tools at runtime and injected into the context. The basis of Retrieval-Augmented Generation (RAG), which we'll cover in Module 7.

**SE parallel**: This maps directly to a caching hierarchy. Parametric knowledge is the L3 cache — large, slow to update, eventually stale. Contextual knowledge is L1 — small, fast, always current. Retrieved knowledge is a cache-aside read from the database — costs a round trip, but gives you the latest data. Every agentic system navigates this hierarchy.

## Models Are Not Monolithic

Not all LLMs are the same, and the differences matter for system design. Key dimensions:

**Size and capability**: Models range from ~1B parameters (fast, cheap, limited) to 1T+ parameters (slow, expensive, highly capable). Larger models generally reason better, follow complex instructions more reliably, and handle longer contexts more coherently. This isn't just academic — the choice between a small and large model is a latency/cost/quality trade-off you'll make constantly.

**SE parallel**: This is the microservice sizing decision. A lightweight service handles simple requests fast and cheap. A heavyweight service handles complex orchestration but costs more per request. You wouldn't route every request through your most expensive service — you'd use intelligent routing. The same logic applies to model selection, and it's formalized as the Router Agent pattern in Part 3.

**Modalities**: Some models handle only text. Others handle text + images (multimodal). Some can generate images or audio. For agentic systems, multimodal capabilities matter because agents often need to interpret screenshots, diagrams, or visual output.

**Open-source vs. proprietary**: Open-source models (Llama, Mistral, Qwen) can be self-hosted, giving you full control over data, latency, and cost. Proprietary models (Claude, GPT) offer higher capability but run as managed services. Most production agentic systems use a mix — proprietary models for complex reasoning, open-source for high-volume simple tasks.

**SE parallel**: Build vs. buy. Self-hosting gives you control at the cost of operational burden (like running your own Postgres vs. using RDS). The answer is almost always "both" at scale.

## The Transformer Architecture (What You Need to Know)

You don't need to understand backpropagation to design agentic systems, but you need a mental model of how transformers process information, because it explains constraints you'll hit constantly.

The key mechanism is **self-attention**: for every token in the input, the model computes how much that token should "attend to" every other token. This is how the model understands that "it" in "The server crashed because it ran out of memory" refers to "server" and not "memory."

The critical implication: self-attention is **O(n^2)** in the sequence length. Doubling your context window quadruples the compute for the attention step. This is why context windows have limits, why longer prompts cost more, and why there's an entire family of context management patterns in this course. Techniques like sparse attention, sliding window attention, and various architectural innovations reduce this in practice, but the fundamental quadratic relationship shapes every design decision about context.

**SE parallel**: It's the N+1 query problem at a mathematical level. Every token "queries" every other token. Architectural solutions (sparse attention, flash attention) are analogous to query optimization strategies — batching, indexing, reducing the working set.

## Why This Foundation Matters for Agents

Every concept in this module maps to a design constraint you'll encounter when building agents:

- **Statelessness** drives the need for external state management (Module 7: Memory & Context)
- **Token-based pricing** drives cost optimization patterns (Module 2: Economics of Inference)
- **Context window limits** drive compression and retrieval patterns (Module 7: Memory & Context)
- **Nondeterminism** drives reliability patterns (Module 14: Reliability Engineering)
- **Knowledge cutoff** drives tool use patterns (Module 6: Tool Use)
- **Quadratic attention cost** drives context minimization patterns (Module 7)
- **Model size trade-offs** drive routing and orchestration patterns (Modules 9-11)

An LLM is not a magic black box. It's a computational primitive with well-defined capabilities, constraints, and failure modes — like a database engine, a message queue, or any other infrastructure component you'd design around.

## Key Takeaways

1. An LLM is a stateless function: tokens in, probability distribution out. All state management is your problem.
2. The context window is your RAM budget — everything the model can "think about" must fit inside it, and it costs O(n^2) to process.
3. Models have parametric knowledge (frozen at training), contextual knowledge (what you send in the prompt), and retrieved knowledge (fetched at runtime). Agents navigate all three.
4. Temperature controls the determinism/creativity trade-off — low for actions, moderate for planning.
5. Model selection is a cost/latency/quality trade-off analogous to microservice sizing. Production systems use multiple models.

## Try This

Open any LLM API (Claude, GPT, or a locally-hosted model via Ollama). Send the same prompt three times with temperature=0, then three times with temperature=1.0. Observe:
- At temperature 0, are the responses identical? (They should be, or nearly so.)
- At temperature 1.0, how much do they diverge?
- Now try a factual question ("What is the capital of France?") vs. an open-ended question ("Write a function name for a cache invalidation method"). Which benefits more from higher temperature?

This exercise builds intuition for when determinism matters — critical for tool-calling agents where you need predictable structured output.

## System Design Question

You're designing a system where an agent needs to process a 500-page technical document and answer questions about it. The document is ~250K tokens. Your model has a 200K-token context window. What are your options, and what are the trade-offs of each? Think in terms of the caching hierarchy (parametric, contextual, retrieved knowledge) introduced in this module.
