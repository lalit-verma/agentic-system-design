# Module 6: Tool Use Patterns

**Software engineering parallel**: API design and integration patterns — how you build, discover, select, and invoke services in a distributed system. The quality of your tool design determines whether the agent is a productive developer or a confused intern.

**Patterns covered**: LLM-Friendly API Design, Dual-Use Tool Design, Shell Command Contextualization, Progressive Tool Discovery, Code Mode MCP Tool Interface, Agent SDK for Programmatic Control, CLI-Native Agent Orchestration, CLI-First Skill Design, Code-Then-Execute, CodeAct Agent, Dynamic Code Injection, Code-Over-API, Intelligent Bash Tool Execution, Action-Selector, Tool Use Steering via Prompting, Patch Steering via Prompted Tool Selection, Agentic Search Over Vector Embeddings, Visual AI Multimodal Integration, Conditional Parallel Tool Execution

---

## The Core Insight

Tools turn a chatbot into an agent (Module 4). But not all tool designs are equally effective. An LLM interacts with tools through natural language descriptions and structured schemas — it can't read source code documentation the way a human developer does. Tool design for agents is a distinct discipline with its own patterns.

This module covers 19 patterns organized into four groups: how you design tools, how agents execute code, how agents select tools, and specialized tool capabilities.

## Group 1: Tool Design Patterns

These patterns govern how you build tools that LLMs can actually use well.

### LLM-Friendly API Design

**What it does**: Designs tool interfaces specifically for LLM consumption — clear names, unambiguous descriptions, constrained parameter types, and explicit error messages.

**SE parallel**: Developer experience (DX) in API design. The same principles that make APIs pleasant for human developers — consistent naming, good error messages, sensible defaults — make them usable for LLMs. Except LLMs are more literal and less forgiving of ambiguity.

**Concrete guidelines**:
- Tool names should be verbs: `read_file`, not `file` or `file_reader`.
- Descriptions should say *when* to use the tool, not just *what* it does: "Read a file from disk. Use this when you need to see file contents. Use Glob to find files by pattern instead."
- Parameters should be typed tightly: use enums over free strings, require absolute paths, avoid boolean flags that change behavior entirely.
- Error messages should suggest next steps: "File not found at /src/foo.py. Did you mean /src/lib/foo.py?" rather than "ENOENT."

**When it fails**: Vague descriptions lead to misuse. A tool described as "search" will be called for both file search and web search. A parameter named `options` with no schema will be filled with hallucinated arguments.

### Dual-Use Tool Design

**What it does**: Designs tools that serve both human users and LLM agents through the same interface.

**SE parallel**: APIs serving both humans (via UI) and machines (via SDK). You design one API but ensure it works for both consumers — human-readable responses for the UI, machine-parseable responses for the SDK.

**How it works**: Every tool has a structured output (JSON for the agent) and can optionally render a human-readable version (formatted text for display). The same `run_tests` tool returns structured pass/fail results for the agent and a readable test report for the human watching the agent work.

**When to use it**: Any tool in a human-in-the-loop agent. The human needs to understand what the agent is doing; the agent needs to parse the results. Separate tools for each consumer is wasteful.

### Shell Command Contextualization

**What it does**: Wraps raw shell commands with descriptions, examples, and guardrails so the LLM uses them correctly.

**SE parallel**: Man pages / `--help`. The shell is powerful but dangerous — `rm -rf /` is syntactically valid. Contextualization is like wrapping raw system calls in a safe API: the agent can run shell commands, but the tool description tells it which commands are safe, provides usage examples, and warns about destructive operations.

**How it works**: Instead of a bare `execute_shell(command)` tool, provide context in the description: "Execute a bash command. Safe for: git operations, file manipulation, running tests. Requires approval for: installing packages, modifying system files. Never: delete directories outside the project root."

### Progressive Tool Discovery

**What it does**: Instead of loading all available tools at startup, reveals tools as they become relevant to the task.

**SE parallel**: Service discovery / DNS. In a microservice architecture, services don't hardcode all other service endpoints at startup — they discover available services dynamically. Similarly, an agent with 50 available tools shouldn't see all 50 in every prompt — it should discover the relevant ones based on context.

**Why it matters**: Every tool definition in the system prompt consumes tokens (cost) and dilutes attention (quality). An agent with 5 relevant tools in context performs better than one with 50 mostly-irrelevant tools. Loading tools on-demand keeps the context lean.

**Implementation**: Start with core tools (read, write, search). When the agent encounters a task that requires additional capability (e.g., database queries), dynamically inject the database tool definitions. The model either requests tools explicitly ("I need a tool for querying PostgreSQL") or the runtime detects the need heuristically.

### Code Mode MCP Tool Interface

**What it does**: Standardizes tool definition and invocation using the Model Context Protocol (MCP) — a protocol for connecting agents to external tool servers via a typed interface.

**SE parallel**: gRPC + protobuf. Just as gRPC defines a standard way to describe and invoke services with strong typing and code generation, MCP defines a standard way to describe and invoke tools. Tool providers publish MCP-compliant servers; agent runtimes connect to them as clients.

**When to use it**: When you want interoperability — tools built once can be used by any MCP-compatible agent. This is the tool equivalent of REST APIs: a shared contract that enables an ecosystem. The trade-off is the abstraction overhead; for tightly integrated systems, direct tool calls are simpler.

### Agent SDK for Programmatic Control

**What it does**: Provides a programming interface (SDK) for building, configuring, and controlling agents from application code.

**SE parallel**: Client SDKs (AWS SDK, Stripe SDK). Instead of making raw HTTP calls, you use a typed library that handles authentication, serialization, retries, and error handling. Agent SDKs do the same for agent creation — providing typed interfaces for tool registration, model selection, memory configuration, and loop control.

**When to use it**: When building agents into larger applications. The SDK abstracts the agent loop, letting developers focus on tool definitions and business logic rather than prompt engineering and message management.

## Group 2: Code Execution Patterns

These patterns address the most powerful tool capability: having the agent write and execute code.

### Code-Then-Execute

**What it does**: The agent writes a code snippet, then immediately executes it and observes the result. This is the fundamental pattern behind REPL-driven agent development.

**SE parallel**: Compile-and-run / REPL. Write code, run it, see the output, iterate. The same feedback loop developers use interactively, but automated within the agent loop.

**How it works**: The agent generates code (a function, a script, a shell command), the runtime executes it in a sandbox, and the output is fed back as a tool result. The agent reads the output and decides whether to iterate (fix errors, adjust approach) or proceed.

**Scenario**: An agent asked to analyze a dataset. Instead of trying to reason about the data from descriptions, it writes a Python script that loads the data, computes statistics, and prints results. It reads the output and writes the summary. The code is the tool.

### CodeAct Agent

**What it does**: Uses code as the primary action language instead of predefined tool calls. Rather than calling `read_file(path)`, the agent writes `open(path).read()` in Python and executes it.

**SE parallel**: Stored procedures / server-side scripting. Instead of calling individual API endpoints, you push a script to the server that combines multiple operations. CodeAct pushes a code block to the runtime that can do anything — read files, call APIs, transform data — in a single execution.

**Advantages**: The agent can compose operations that no predefined tool supports. It can loop, branch, and combine operations in ways that individual tool calls can't express. It's the most flexible tool pattern.

**Trade-off**: Security and containment are harder. Code can do anything the runtime allows — so the sandbox becomes critical. This pattern requires strong isolation (Module 15: Security).

### Dynamic Code Injection

**What it does**: The agent generates code that modifies its own runtime — adding new functions, tools, or capabilities on the fly.

**SE parallel**: Hot module replacement / plugins. Like a server that can load new middleware without restarting, the agent can generate and register new tools during execution.

**Scenario**: An agent working with an unfamiliar API generates a wrapper function based on the API documentation, registers it as a new tool, and uses it for the rest of the session. The tool didn't exist when the session started.

**Trade-off**: Same security concerns as CodeAct, amplified. Generated code that modifies the runtime needs careful sandboxing. This is an advanced pattern — powerful but requiring mature security infrastructure.

### Code-Over-API Pattern

**What it does**: Prefers having the agent write code that calls libraries directly rather than routing through agent API tools. For example, using `pandas.read_csv()` directly rather than a custom `read_csv` tool.

**SE parallel**: Stored procedures vs. API calls. Sometimes calling the database directly is more efficient than going through an API layer. Code-Over-API applies when the overhead of tool abstraction exceeds the safety benefit.

**When to use it**: When the agent works in a sandboxed environment where direct code execution is safe, and the available libraries provide richer functionality than your predefined tools. Common in data science and analysis tasks.

### Intelligent Bash Tool Execution

**What it does**: Wraps shell command execution with intelligence — understanding the command context, providing appropriate working directories, handling environment variables, and interpreting output.

**SE parallel**: Smart build systems (Make, Gradle). They don't just run commands — they understand dependencies, manage state, and provide meaningful output. An intelligent bash executor sets up the context, interprets errors, and suggests fixes rather than just returning raw stderr.

## Group 3: Tool Selection and Routing Patterns

These patterns address how the agent decides *which* tool to use.

### Action-Selector Pattern

**What it does**: The LLM chooses from a structured menu of available actions on each turn, rather than free-form generation.

**SE parallel**: Strategy pattern / command pattern (GoF). Each action is a self-contained command object. The LLM acts as the selector, choosing which command to execute based on context.

**How it works**: Present the LLM with an explicit list of available actions and their preconditions. The LLM selects one and provides the arguments. This reduces hallucination (the model can't invent actions that don't exist) and simplifies parsing (the output is always a selection from a known set).

### Tool Use Steering via Prompting

**What it does**: Guides the LLM toward correct tool selection through system prompt instructions — "prefer Grep over Bash for searching code," "use Read instead of cat."

**SE parallel**: Hinting query optimizers. Database optimizer hints (`/*+ INDEX(table idx_name) */`) guide the planner toward better execution plans without changing the query logic. Tool steering hints guide the agent toward better tool choices without changing the task.

**Why it matters**: LLMs have default preferences based on training data. Without steering, an agent might use `grep` (via bash) when a dedicated search tool would be more reliable and produce better-structured output. Prompt-based steering corrects these defaults.

### Patch Steering via Prompted Tool Selection

**What it does**: Guides the agent toward specific tools for code modification tasks — preferring surgical edits (search-and-replace) over full file rewrites.

**SE parallel**: Content-based routing. Route the request to the handler best suited for the payload. Small, targeted changes route to an edit tool; large rewrites route to a write tool. The system prompt encodes these routing rules.

**Scenario**: An agent tasked with renaming a variable. Without steering, it might rewrite the entire file. With patch steering, it uses a search-and-replace tool that modifies only the relevant lines — faster, safer, and producing cleaner diffs.

## Group 4: Specialized Tool Capabilities

### Agentic Search Over Vector Embeddings

**What it does**: The agent uses semantic search (vector similarity) as a tool to find relevant code, documents, or knowledge that keyword search would miss.

**SE parallel**: Inverted index + vector index. Traditional search finds exact matches; vector search finds conceptual matches. "Functions that handle authentication" finds results even if they never use the word "authentication." The agent combines both search types strategically.

### Visual AI Multimodal Integration

**What it does**: The agent uses vision capabilities to interpret screenshots, diagrams, error visuals, and UI renderings as part of its reasoning.

**SE parallel**: Multi-format content pipelines. Just as a content pipeline processes text, images, and video through format-specific handlers, multimodal integration lets the agent read a screenshot of a broken UI, understand what's wrong, and generate the CSS fix.

**When to use it**: UI development, debugging visual regressions, interpreting error screenshots, working with diagrams or architecture documents. This pattern requires a multimodal model (Module 1).

### Conditional Parallel Tool Execution

**What it does**: Executes multiple independent tool calls simultaneously when the results don't depend on each other, with guards that prevent parallel execution when dependencies exist.

**SE parallel**: `async.parallel` with guards. Like `Promise.all()` in JavaScript but with dependency analysis — if tool B needs the result of tool A, run them sequentially; if they're independent, run them in parallel.

**Why it matters**: An agent that reads 5 independent files sequentially takes 5 round trips. With conditional parallel execution, it takes 1 round trip. The savings compound over long sessions. Modern APIs support parallel tool calls natively.

### CLI-Native Agent Orchestration and CLI-First Skill Design

**What it does**: Designs the agent to operate natively through the command line, and structures agent capabilities as composable CLI commands.

**SE parallel**: Unix philosophy — small tools that do one thing well, composed via pipes. `cat file.txt | grep "error" | wc -l`. CLI-native agents follow the same principle: each skill is a discrete, composable command that can be piped, scripted, and automated.

**Why it matters for agents**: CLI interfaces are inherently machine-friendly — structured input/output, predictable behavior, composability. An agent designed as a CLI tool can be orchestrated by scripts, CI pipelines, or other agents. It's the natural interface for developer-facing agents.

## Key Takeaways

1. Tool design for LLMs is a distinct discipline — descriptions must say *when* to use a tool, parameters must be tightly typed, and error messages must be actionable. Bad tool design is the #1 cause of agent failures.
2. Code execution (CodeAct, Code-Then-Execute) is the most powerful tool pattern — the agent can do anything the runtime allows. The trade-off is security: more power demands stronger sandboxing.
3. Progressive Tool Discovery keeps context lean by only showing relevant tools. Every unnecessary tool in the prompt wastes tokens and dilutes attention.
4. Tool selection steering via prompts corrects the LLM's default preferences and routes it toward the right tool for each task type.
5. Conditional parallel tool execution is a straightforward optimization that reduces multi-step latency by running independent operations concurrently.

## Try This

Design a tool set for a coding agent that works with a Python project. Define 5-8 tools with: name, description (including when-to-use guidance), and parameter schema. Then test it: give the agent a task ("find all functions that don't have docstrings and add them") and observe which tools it chooses. Iterate on the descriptions until the agent consistently makes good tool choices. Pay attention to cases where it chooses the wrong tool — that's a tool design failure, not a model failure.

## System Design Question

You're designing a tool registry for a platform that supports third-party tool providers (like MCP servers). Developers publish tools; agents discover and use them. How do you handle: tool versioning (a tool's schema changes), tool quality (some tools have better descriptions than others), tool conflicts (two tools with similar names), and tool security (a malicious tool provider)? Draw parallels to package registry design (npm, PyPI).
