# Module 2: The Economics of Inference

**Software engineering parallel**: Cloud compute pricing — you're buying a metered resource (tokens instead of CPU-seconds) where architecture decisions determine whether your bill is linear or exponential.

**Patterns covered**: None (foundational module — establishes the cost model that drives optimization patterns in later modules)

---

## Why Economics Comes Before Architecture

In traditional software, you can often build first and optimize later. With LLMs, cost is a first-class architectural constraint. A naive agent design can burn through hundreds of dollars in a single session. A well-architected one can do the same work for cents. The difference isn't clever code — it's understanding how inference pricing works and designing around it.

This module gives you the cost model. Every pattern from Module 4 onward will reference it.

## The Two Phases of Inference

When you send a request to an LLM, two distinct computational phases occur. Understanding them separately is essential because they have different cost profiles, different bottlenecks, and different optimization strategies.

### Phase 1: Prefill (Processing Your Input)

The model reads your entire prompt and builds an internal representation of it. This processes all input tokens in parallel — unlike output generation, the model can look at your entire prompt at once. The main cost driver here is the O(n^2) attention computation from Module 1.

**SE parallel**: This is the query planning and index scan phase of a database query. The database reads your query, consults its statistics, builds an execution plan, and scans the relevant indices. It's compute-intensive but parallelizable.

### Phase 2: Decode (Generating the Output)

The model generates output tokens one at a time, autoregressively (as we covered in Module 1). Each token requires a forward pass through the entire model, but only for one new token at a time. This phase is memory-bandwidth-bound rather than compute-bound — the bottleneck is reading the model's weights from GPU memory for each token.

**SE parallel**: This is the row-by-row result streaming phase. The database has done its scan and is now sending rows back to the client one at a time over the network. The bottleneck shifts from CPU to I/O.

### Why the Two Phases Matter

Providers price these phases differently because they cost different things:

- **Input tokens** (prefill): Cheaper per token. Parallelizable. Scales with prompt length squared (attention cost) but processes fast because it's compute-bound and GPUs are good at parallel compute.
- **Output tokens** (decode): More expensive per token (typically 3-5x input price). Sequential. Each token incurs a full model read from memory.

As of early 2026, representative pricing for a frontier model:
- Input: ~$3 per million tokens
- Output: ~$15 per million tokens

This asymmetry is not arbitrary — it reflects the underlying hardware economics. And it directly shapes how you design agents: **it's much cheaper to give an agent a long, detailed prompt than to have it generate a long, rambling response.**

## The KV Cache: Why Conversations Get Expensive

During the prefill phase, the model computes intermediate values for each token called **key-value pairs** (the K and V in the attention mechanism). These get stored in a **KV cache** so they don't need to be recomputed when generating each output token.

Here's the critical implication for agent design: in a multi-turn conversation, the entire conversation history is re-processed on every turn. Turn 1 processes N tokens. Turn 2 processes N + response_1 + new_prompt tokens. Turn 10 might be processing 50K+ tokens of accumulated history, even though only the last message is "new."

**SE parallel**: Imagine a REST API where every request must include the complete session transcript. It's as if your HTTP request body grows linearly with session duration — and you're paying per byte, with the processing cost growing quadratically. This is the economic pressure behind the Context Window Auto-Compaction and Context-Minimization patterns in Module 7.

### Prompt Caching: The Optimization

Providers have responded with **prompt caching**: if the beginning of your prompt is identical to a recent request (exact byte-for-byte prefix match), the provider can reuse the cached KV pairs and skip the prefill computation for that prefix. Cached input tokens are typically priced at 90% discount.

This creates a concrete architectural incentive: **keep your system prompt and static context at the beginning of every request, and put variable content at the end.** Any prefix that matches gets the cache discount.

**SE parallel**: This is literally CDN edge caching. The "origin" is the full prefill computation. The "cache key" is the exact byte prefix. Cache hits are cheap and fast. Cache misses are expensive. Your architecture should maximize cache hit rate — same principle as designing for HTTP cache headers, just applied to prompt structure. This becomes the Prompt Caching via Exact Prefix Preservation pattern in Module 7.

## Cost Anatomy of an Agent Session

Let's make this concrete. Consider a coding agent that:
1. Receives a task description (500 tokens)
2. Reads a system prompt with instructions (2,000 tokens)
3. Reads 5 files to understand context (15,000 tokens)
4. Reasons about the approach (generates 1,000 tokens)
5. Writes code changes (generates 2,000 tokens)
6. Reads test output (3,000 tokens)
7. Fixes a bug based on test failure (generates 1,500 tokens)

Naive cost calculation at $3/$15 per million tokens:

| Step | Input tokens (cumulative) | Output tokens | Input cost | Output cost |
|------|---------------------------|---------------|------------|-------------|
| 1-3  | 17,500                    | 0             | $0.05      | $0.00       |
| 4    | 17,500                    | 1,000         | $0.05      | $0.015      |
| 5    | 18,500                    | 2,000         | $0.06      | $0.03       |
| 6    | 23,500                    | 0             | $0.07      | $0.00       |
| 7    | 23,500                    | 1,500         | $0.07      | $0.02       |

Total for this simple 7-step session: ~$0.37. That's one straightforward bug fix. A complex feature might take 50-100 steps with much larger context, easily reaching $5-20 per session. At scale — dozens of developers running agents all day — you're looking at infrastructure-level spend.

The numbers shift dramatically with prompt caching. If the system prompt (2,000 tokens) and file contents (15,000 tokens) are cache-hit on steps 4-7, the cumulative input cost drops substantially because those 17,000 tokens are re-processed at a 90% discount.

## Thinking Tokens: Paying for Reasoning

Modern frontier models offer **extended thinking** (sometimes called "reasoning" or "chain-of-thought" mode). When enabled, the model generates internal reasoning tokens before producing its visible response. These thinking tokens are billed as output tokens — at the expensive output rate.

A model might generate 5,000 thinking tokens to work through a complex coding problem, then produce 500 tokens of actual code. You're paying output rates for all 5,500 tokens, but only 500 are your "real" result. The thinking tokens are invisible in the response but very visible on the invoice.

**SE parallel**: This is like enabling query plan analysis (`EXPLAIN ANALYZE`) on every database query. You get better results because the optimizer works harder, but the compute cost increases. The question is whether the quality improvement justifies the cost — and for complex tasks, it usually does. For simple tasks, it's waste.

This creates the design question: when should your agent use extended thinking? The answer maps to the Inference-Time Scaling pattern (Module 5) — spend more compute on hard problems, less on easy ones. A model routing layer that classifies task difficulty and enables thinking only for complex tasks can cut reasoning costs by 60-80%.

## Latency: The Other Cost

Token cost isn't the only economic factor. Latency directly affects user experience and system throughput.

**Time to first token (TTFT)**: How long before the first output token appears. Dominated by prefill time. Longer prompts = longer TTFT. A 100K-token prompt might take 5-10 seconds just for prefill.

**Tokens per second (TPS)**: Output generation speed. Typically 30-100 tokens/second for frontier models via API. A 2,000-token response takes 20-60 seconds to generate.

**End-to-end latency for an agent step**: TTFT + (output_tokens / TPS). For the coding agent example above, each step might take 10-30 seconds. A 50-step session is 8-25 minutes of wall clock time, even if the "work" is simple.

**SE parallel**: This maps to the request latency decomposition you'd do for any service: network round trip + server processing time + payload transfer. The difference is that LLM "processing time" is extraordinarily long compared to traditional APIs — seconds to minutes instead of milliseconds. This forces asynchronous patterns: you can't hold an HTTP connection open for 25 minutes.

### Batching and Throughput

Providers can serve multiple requests concurrently on the same GPU hardware. From a provider's perspective, the economics favor batching — filling GPU utilization by processing many requests simultaneously. This is why API pricing is much cheaper per token than running your own hardware: you're sharing the GPU with other customers.

**SE parallel**: Multi-tenant database hosting. Shared infrastructure is cheaper per tenant because idle capacity is filled by other tenants. But you lose isolation — noisy neighbors can affect your latency during peak periods.

## The Build vs. Buy Decision for Inference

You have three options for inference infrastructure:

### Option 1: API providers (OpenAI, Anthropic, Google)
- **Cost model**: Pay per token, no upfront commitment.
- **Advantages**: Zero ops burden, automatic scaling, access to frontier models.
- **Disadvantages**: Per-token cost at scale, data leaves your network, rate limits, provider dependency.
- **When**: Starting out, variable/unpredictable load, need frontier model capability.

### Option 2: Self-hosted open-source models
- **Cost model**: GPU hardware (owned or rented) + ops overhead.
- **Advantages**: Fixed cost (predictable budgets), data stays local, no rate limits, full customization.
- **Disadvantages**: Lower model capability, significant ops burden, GPU procurement lead times.
- **When**: High-volume simple tasks, strict data residency, need for fine-tuned models.

### Option 3: Hybrid
- **Cost model**: Mix of per-token and fixed infrastructure.
- **Advantages**: Route simple tasks to cheap self-hosted models, complex tasks to frontier APIs.
- **Disadvantages**: Operational complexity of managing two systems plus a routing layer.
- **When**: At scale, once you understand your workload distribution. This is where most production systems land.

**SE parallel**: This is the classic cloud compute decision. On-demand EC2 (API per-token) vs. reserved instances (self-hosted GPU) vs. a mix. The break-even point depends on utilization — same as with GPU inference. Low, variable utilization favors per-token. High, steady utilization favors self-hosted. The routing layer that makes the hybrid work is the Router Agent pattern (Module 9) applied to infrastructure.

## Cost Optimization Levers

In order of impact, here's what moves the needle on inference cost:

### 1. Reduce what you send (context minimization)
Every token in your prompt costs money and attention compute. Don't send the agent an entire file when it only needs a function. Don't include conversation history that's no longer relevant. This is the single highest-impact optimization and the motivation behind an entire family of patterns: Context-Minimization, Semantic Context Filtering, Progressive Disclosure for Large Files (all Module 7).

### 2. Use the right model for the task
A $0.25/M-token model can handle classification, extraction, and simple formatting. A $15/M-token model is needed for complex multi-step reasoning. Routing every task to the most powerful model is like running every SQL query on your most expensive database cluster. The Budget-Aware Model Routing pattern (Module 11) formalizes this.

### 3. Maximize prompt cache hits
Structure your prompts so the static prefix is as long and stable as possible. A 90% cache discount on 80% of your input tokens is a massive cost reduction. This requires disciplined prompt architecture — not dynamic generation of the full prompt each time.

### 4. Control output length
Output tokens are 3-5x more expensive than input. Use system prompts that enforce concise responses. For structured outputs, define schemas that prevent verbose explanations when you only need JSON. Don't let the model explain its reasoning in production when you only need the answer (save extended thinking for genuinely hard tasks).

### 5. Batch where possible
If your agent needs to process 100 items, don't make 100 serial API calls. Use batch APIs (most providers offer these at 50% discount) for non-latency-sensitive work. This is the same optimization as batching database writes.

## The Economics Shape the Architecture

Here's the key insight to carry forward: LLM inference cost isn't an afterthought — it's a structural force that shapes every architectural decision in agentic systems.

- **Why agents have memory systems**: Because re-reading everything from scratch every turn is prohibitively expensive (Module 7).
- **Why multi-agent systems use model routing**: Because not every subtask justifies a frontier model (Module 9).
- **Why context windows need management**: Because every extra token costs money and degrades attention quality (Module 7).
- **Why agents need tools**: Because generating information is expensive — looking it up in a database is cheap (Module 6).
- **Why feedback loops matter**: Because wasting a $5 agent session on a wrong approach is expensive — catching mistakes early is an economic imperative (Module 12).

The cost model is not a constraint to work around. It's a design force to work with, the same way database I/O cost shapes schema design and query patterns.

## Key Takeaways

1. Input tokens are cheap and parallelizable; output tokens are 3-5x more expensive and sequential. Design prompts to be input-heavy and output-lean.
2. Conversation cost grows with accumulated context — every turn re-processes the full history. This is the economic driver for context management patterns.
3. Prompt caching (exact prefix match) can reduce input costs by up to 90%. Prompt structure should be designed for cache hits.
4. Extended thinking tokens are billed as output — powerful but expensive. Use them selectively based on task complexity.
5. The build/buy/hybrid decision for inference follows the same economics as cloud compute: utilization-dependent break-even points.

## Try This

Use any LLM API with usage tracking (most dashboards show token counts per request). Run the same task two ways:
1. **Verbose prompt**: Include full file contents, detailed instructions, examples, and ask for a detailed explanation with the answer.
2. **Lean prompt**: Include only the relevant code section, concise instructions, and ask for only the answer in a specific format.

Compare: token counts (input and output), cost, latency, and — crucially — answer quality. In many cases, the lean prompt produces equal or better results. When it doesn't, that delta is the actual value of the extra context — and you can decide whether it's worth paying for.

## System Design Question

You're designing a coding agent that will be used by 50 developers, each running ~20 agent sessions per day, with an average session involving 30 agent turns. Each turn processes an average of 20K input tokens and generates 1K output tokens. Assume pricing of $3/M input tokens and $15/M output tokens.

Calculate the monthly cost. Then propose three architectural changes — referencing concepts from this module — that could reduce the cost by at least 50%, and explain the trade-offs of each.
