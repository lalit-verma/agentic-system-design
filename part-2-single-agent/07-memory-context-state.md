# Module 7: Memory, Context & State

**Software engineering parallel**: The storage hierarchy — CPU registers, L1/L2/L3 cache, RAM, SSD, cold storage. Each tier trades capacity for speed and cost. Agent memory management is the same problem: what to keep close, what to page out, what to persist, and how to retrieve it when needed.

**Patterns covered**: Context Window Auto-Compaction, Context-Minimization Pattern, Curated Code/File Context Window, Progressive Disclosure for Large Files, Semantic Context Filtering, Prompt Caching via Exact Prefix Preservation, Dynamic Context Injection, Layered Configuration Context, Hierarchical Memory — Working/Main/Archive, Working Memory via TodoWrite, RAG — Retrieval-Augmented Generation, Episodic Memory Retrieval & Injection, Memory Synthesis from Execution Logs, Filesystem-Based Agent State, Proactive Agent State Externalization, Self-Identity Accumulation, Agent-Powered Codebase Q&A / Onboarding

---

## The Central Problem

An LLM is stateless (Module 1). It forgets everything between calls. Yet an agent needs to maintain coherent state across dozens or hundreds of turns — remembering what files it has read, what decisions it has made, what the user asked 20 turns ago, and what it learned from past sessions.

Meanwhile, every token of context costs money and processing time (Module 2), and the context window has a hard limit. You can't just dump everything in.

This module addresses the fundamental tension: **how to give the agent the right context at the right time without exceeding the budget.** The 17 patterns here divide into four groups: shrinking context (make what you send smaller), structuring context (organize what you send), managing memory tiers (short-term vs. long-term), and persisting state (surviving across sessions).

## Group 1: Context Budget Management

These patterns reduce the cost and improve the quality of what you send to the model on each turn.

### Context-Minimization Pattern

**What it does**: Sends only the minimum context needed for the current step. Every token must earn its place in the prompt.

**SE parallel**: Payload optimization / lean DTOs. You don't send the entire database row when the client only needs two fields. You project only the necessary columns. Context-Minimization applies the same discipline to prompts.

**Implementation**: Before each LLM call, ask: "What does the model need to know to complete *this specific step*?" If it's writing a function, it needs the function signature and relevant types — not the entire file. If it's fixing a test, it needs the failing test and the function under test — not the full test suite.

**Why it's the highest-impact pattern**: Module 2 showed that context grows quadratically in attention cost. Cutting context by 50% doesn't save 50% — it saves 75% of attention compute. And smaller context means the model focuses better on what matters, improving output quality.

### Context Window Auto-Compaction

**What it does**: Automatically summarizes or truncates older conversation history when the context approaches its limit, preserving the most important information.

**SE parallel**: Buffer pool eviction / LRU cache. When the buffer pool is full and a new page needs loading, the least-recently-used page gets evicted. Auto-compaction does the same — when context is full, older turns get summarized (lossy compression) or dropped (eviction) to make room for new information.

**How it works**: Monitor context usage. When it exceeds a threshold (e.g., 80% of the window), trigger compaction:
1. Summarize older turns into a compact "session summary" paragraph
2. Keep recent turns verbatim (they contain the most relevant context)
3. Preserve tool results that are still being referenced
4. Replace verbose tool outputs with compact summaries

**Trade-off**: Summarization is lossy. The agent may lose details from early turns that become relevant later. Aggressive compaction saves cost but risks the agent "forgetting" important context. The sweet spot depends on task type — exploratory tasks need longer memory, focused tasks can compact aggressively.

### Curated Code/File Context Window

**What it does**: Selects specific code sections to include in context rather than dumping entire files. Reads the function, not the file.

**SE parallel**: Selective cache warming. You don't load every database table into cache at startup — you warm the cache with the specific data your hot path needs. Curated context loads only the code relevant to the current task.

**Implementation**: Use AST parsing, regex extraction, or a lightweight search to identify the relevant code sections. Include: the target function, its callers, its dependencies, and relevant type definitions. Exclude: unrelated functions in the same file, comments that aren't relevant, boilerplate imports.

### Progressive Disclosure for Large Files

**What it does**: Shows the agent a file summary first, then loads specific sections on demand — never the whole file at once.

**SE parallel**: Pagination / streaming responses. An API doesn't return 10,000 rows in one response — it paginates. Progressive disclosure paginates files for the agent: first show the outline (function signatures, class structure), then load specific sections the agent requests.

**How it works**: Step 1 — show the file's structure (class names, function signatures, line count). Step 2 — the agent identifies what it needs ("I need to see lines 45-80, the `validate_input` function"). Step 3 — load that section. This keeps each step's context small while giving the agent full access to the file's contents.

### Semantic Context Filtering

**What it does**: Uses semantic similarity (embeddings) to select which prior context is relevant to the current step, rather than using recency alone.

**SE parallel**: Query optimization / index selection. A database doesn't scan every row — it uses indices to find relevant rows. Semantic filtering creates a "semantic index" over context chunks and retrieves only those relevant to the current query.

**How it works**: Embed each conversation turn, tool result, and loaded file. When composing the next prompt, embed the current task, find the K most semantically similar context chunks, and include only those. A turn about database configuration from 30 turns ago re-surfaces when the current task involves database changes — even though recency-based selection would have dropped it.

## Group 2: Context Structure and Injection

These patterns govern how context is organized and delivered to the model.

### Prompt Caching via Exact Prefix Preservation

**What it does**: Structures prompts so that the static prefix (system prompt, tool definitions, project context) remains byte-identical across turns, maximizing prompt cache hits.

**SE parallel**: HTTP cache / CDN edge caching (as previewed in Module 2). The cache key is the exact byte prefix. Any change — even a single character — invalidates the cache for everything after that point.

**Implementation rules**:
1. System prompt goes first. Never modify it mid-session.
2. Tool definitions go second. Register all tools at startup; don't add/remove mid-session if possible.
3. Static project context (CLAUDE.md, repo structure) goes third.
4. Conversation history goes last — it's the only part that changes.

**Impact**: With a well-structured prompt where 70% of the content is static, you save ~63% on input costs (70% × 90% cache discount). Over thousands of turns, this is the single biggest cost lever.

### Dynamic Context Injection

**What it does**: Loads context on-demand based on the current task, rather than including everything upfront.

**SE parallel**: Lazy loading / dependency injection. A web page doesn't load every image at startup — it lazy-loads images as the user scrolls. Dynamic injection loads relevant files, documentation, or knowledge only when the agent needs them.

**How it works**: The agent's system prompt contains rules about when to inject context. Example: "When modifying a file, first read the file to understand current contents." The runtime can also inject context proactively — when the agent is about to modify `auth.py`, automatically inject the project's authentication documentation.

### Layered Configuration Context

**What it does**: Organizes context into layers with clear precedence, like a configuration hierarchy.

**SE parallel**: Hierarchical config — env vars > config file > defaults. In most applications, configuration comes from multiple sources with defined override rules. Layered context applies the same principle: global defaults (system prompt) < project settings (CLAUDE.md) < session context (conversation history) < immediate context (current tool results).

**Implementation**: The agent's prompt is assembled from layers. A project-level instruction like "always use TypeScript" overrides the global default. A session-specific instruction like "for this task, write in Python" overrides the project level. The model sees all layers and applies the highest-priority instruction when they conflict.

## Group 3: Memory Tiers

These patterns manage information that persists beyond the current turn.

### Hierarchical Memory — Working/Main/Archive

**What it does**: Structures agent memory into three tiers with different capacity, cost, and access patterns.

**SE parallel**: CPU cache hierarchy (L1/L2/L3) or storage tiering (SSD/HDD/S3). Fast, small, expensive at the top; slow, large, cheap at the bottom. Data flows between tiers based on access patterns.

**The three tiers**:
- **Working memory** (L1): The current context window. Small (200K tokens), expensive per token, always available to the model. Contains the current conversation, recent tool results, active task state.
- **Main memory** (L2): Information from the current session that's been compacted out of the context window. Medium capacity, stored in the runtime's memory. Retrieved by semantic search or explicit request. Example: a file the agent read 30 turns ago — summarized in working memory, full text available in main memory if needed.
- **Archive memory** (L3): Information that persists across sessions. Large capacity, stored on disk or in a database. Contains past session summaries, user preferences, project-specific knowledge. Retrieved selectively and injected when relevant.

### Working Memory via TodoWrite

**What it does**: Maintains a structured task list as a persistent scratchpad that the agent reads at the beginning of each turn and updates as it works.

**SE parallel**: In-process task queues. A worker reads from its task queue, processes the next item, updates the queue state. The todo list serves the same function — it's a structured representation of "what I'm doing, what's done, what's next" that survives context compaction because it's updated explicitly.

**Why it matters**: Without explicit working memory, the agent relies on conversation history to remember its plan — which gets expensive and eventually compacted away. A todo list is a compact, structured representation of the agent's current state that costs far fewer tokens than the conversation turns that produced it.

### RAG — Retrieval-Augmented Generation

**What it does**: Supplements the model's parametric knowledge with information retrieved from an external knowledge store at query time. The model searches a knowledge base, retrieves relevant documents, and includes them in its context before generating a response.

**SE parallel**: Cache-aside / read-through cache + search index. The application checks the cache first (parametric knowledge). On a miss, it queries the database (knowledge store), puts the result in the cache (context window), and returns it. RAG is this pattern applied to LLM knowledge gaps.

**How it works**:
1. Index your knowledge base (documents, code, FAQs) by computing vector embeddings (Module 6).
2. When the agent receives a query, embed the query and find the K most similar documents.
3. Inject those documents into the prompt as additional context.
4. The model generates its response informed by both parametric knowledge and retrieved documents.

**When to use it**: Whenever the agent needs to work with information that isn't in its training data — proprietary codebases, internal documentation, recent data. RAG is the bridge between the knowledge cutoff (Module 1) and current information.

**Trade-off**: Retrieved documents consume context window tokens. Retrieve too many and you waste budget; too few and you miss important context. The retrieval quality (precision and recall) determines RAG effectiveness — bad retrieval produces irrelevant context that confuses the model.

### Episodic Memory Retrieval & Injection

**What it does**: Stores and retrieves specific past experiences (tool invocations, decisions, outcomes) rather than general knowledge. When the agent encounters a similar situation, it retrieves relevant past episodes.

**SE parallel**: Event sourcing / audit logs. Past events are stored as an immutable log. When the current situation matches a past pattern, the relevant events are replayed to inform the current decision.

**Scenario**: The agent fixed a circular import bug in a project three sessions ago. When it encounters another import error, episodic memory retrieves that past episode — what the error looked like, what the agent did, what worked — and injects it as context. The agent learns from its own experience.

### Memory Synthesis from Execution Logs

**What it does**: Periodically summarizes raw execution history (tool calls, outputs, decisions) into structured knowledge — lessons learned, project patterns, frequently-used files.

**SE parallel**: Log aggregation → dashboards. Raw logs are too voluminous to read. You aggregate them into metrics, patterns, and insights. Memory synthesis does the same: turns hundreds of raw execution steps into compact, reusable knowledge.

### Self-Identity Accumulation

**What it does**: The agent builds a persistent profile over time — preferences, proven approaches, domain knowledge — that shapes its behavior in future sessions.

**SE parallel**: Session affinity / sticky sessions. A load balancer routes returning users to the same server that already has their session state. Self-identity routes an agent to a consistent persona that reflects accumulated experience with this user and project.

**Implementation**: After each session, extract key learnings: "This user prefers TypeScript. Tests live in `__tests__/`. The project uses a custom ORM." Store these in archive memory. Load them at the start of the next session to bootstrap the agent's context.

### Agent-Powered Codebase Q&A / Onboarding

**What it does**: Uses the memory and retrieval system to answer questions about a codebase — "where is authentication handled?", "how does the payment flow work?" — by combining code search, documentation retrieval, and semantic understanding.

**SE parallel**: Documentation-as-code / code search indices. Internal developer tools that make codebases navigable and searchable. The agent acts as an intelligent code search engine that understands intent, not just keywords.

## Group 4: State Persistence

These patterns handle state that must survive session boundaries.

### Filesystem-Based Agent State

**What it does**: Persists agent state (memory, preferences, session data) to the filesystem as structured files — Markdown, JSON, or YAML.

**SE parallel**: Persistent state on disk / write-ahead logs (WAL). The simplest persistence mechanism: write state to a file. It's transparent (human-readable), version-controllable (it's just files), and portable (no database dependency).

**Implementation**: Store memory as Markdown files in a `.agent/` directory. Session summaries, user preferences, project knowledge — all as files that are both human-readable (the user can inspect and edit them) and machine-readable (the agent can load them).

### Proactive Agent State Externalization

**What it does**: The agent actively writes its state to external storage at regular checkpoints — not just at session end, but during execution.

**SE parallel**: Checkpointing in distributed systems. Long-running jobs write checkpoints so they can resume after failure. Proactive externalization does the same: if the agent session crashes at step 30, the state checkpoint lets it resume from step 28 rather than starting over.

**When to use it**: Long-running agent sessions (30+ minutes), expensive operations where re-doing work is costly, and any scenario where session interruption is common (network issues, user disconnects, timeout limits).

## Key Takeaways

1. Context-Minimization is the highest-impact pattern — every unnecessary token costs money quadratically and dilutes model attention. Send only what the current step needs.
2. Prompt Caching via Exact Prefix Preservation is the biggest cost lever — structure prompts so static content stays byte-identical across turns for 90% cache discounts.
3. Hierarchical Memory (working/main/archive) mirrors the hardware storage hierarchy. Working memory is fast and small (context window), main memory is session-scoped, archive memory persists across sessions.
4. RAG bridges the knowledge cutoff gap by retrieving fresh information at query time. It's the standard pattern for grounding agents in proprietary or recent knowledge.
5. State persistence via filesystem or checkpointing enables long-running agents to survive interruptions and accumulate knowledge across sessions.

## Try This

Build a minimal RAG system:
1. Take 10-20 pages of documentation (your own project docs, or any technical documentation).
2. Split them into chunks (~500 tokens each).
3. Compute embeddings for each chunk using any embedding API.
4. For a query, compute the query embedding, find the 3 most similar chunks (cosine similarity), and include them in the prompt.
5. Compare the model's answer with and without RAG — for questions about specific details in the documentation, the difference should be stark.

This gives you hands-on intuition for retrieval quality, chunk sizing, and context budget trade-offs.

## System Design Question

You're designing the memory system for a coding agent that will be used by a team of 20 developers across hundreds of sessions. Each developer works on different parts of a large monorepo. Design the hierarchical memory architecture: What goes in each tier? How does context get promoted or demoted between tiers? How do you handle per-developer vs. project-wide knowledge? What are the storage and retrieval costs, and how do they compare to the inference cost savings from better context?
