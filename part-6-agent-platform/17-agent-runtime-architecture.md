# Module 17: Agent Runtime Architecture

**Software engineering parallel**: Application server internals — the request lifecycle, process isolation model, plugin architecture, session management, and resource governance that make a framework production-ready. This module reverse-engineers how agent runtimes like Claude Code, Cursor, and Devin actually work.

**Patterns covered**: Virtual Machine Operator Agent, Subagent Compilation Checker

---

## What Is an Agent Runtime?

Module 4 defined the agent's six subsystems: system prompt, reasoning engine, tool executor, tool registry, state manager, and stop conditions. That was the logical architecture. This module is the physical architecture — the actual software that implements those subsystems and connects them into a production system.

An **agent runtime** is to an agent what the JVM is to a Java program or Node.js is to a JavaScript application. It's the execution environment that manages the agent's lifecycle, provides infrastructure services (memory, tool execution, security), and mediates between the agent's decisions and the outside world.

**SE parallel**: Think of it as an application server like Tomcat, Express, or Django. The application server handles connection management, request routing, middleware execution, session management, and resource pools. The developer writes handlers (the agent's prompts and tools). The server does everything else.

## Anatomy of a Production Agent Runtime

Let's reverse-engineer what a system like Claude Code actually does, layer by layer.

### Layer 1: The Session Manager

Every agent interaction is a **session** — a bounded scope with its own state, history, and lifecycle. The session manager handles:

**Session creation**: When a user starts an agent session, the runtime:
1. Loads the user's configuration (settings, permissions, preferences)
2. Loads project context (CLAUDE.md, repo structure, memory files)
3. Initializes the tool registry for this project
4. Creates a fresh conversation history
5. Composes the initial system prompt from all these sources (Layered Configuration Context, Module 7)

**Session state**: During execution, the session accumulates:
- Conversation history (messages, tool calls, tool results)
- Working memory (todo lists, tracked files, decisions)
- Token and cost accounting
- Tool execution logs for observability

**Session lifecycle**: The session persists through interruptions (user pauses, network disconnects) and terminates cleanly (persisting relevant state to archive memory, logging metrics).

**SE parallel**: HTTP session management. The session has an ID, state, a timeout, and cleanup logic. The difference is duration — HTTP sessions last seconds; agent sessions last minutes to hours. This requires the same infrastructure as long-running WebSocket connections: heartbeats, reconnection, and state persistence.

### Layer 2: The Prompt Compositor

The system prompt isn't written once — it's assembled dynamically from components on every LLM call. The prompt compositor manages this assembly:

```
Prompt Composition Order (for cache efficiency):

1. Base system prompt        [STATIC — cached]
   Role definition, behavioral rules, output formats

2. Tool definitions          [STATIC — cached]
   All registered tools with schemas and descriptions

3. Project context           [SEMI-STATIC — cached per project]
   CLAUDE.md, repo structure, coding conventions

4. Memory injection          [DYNAMIC]
   Relevant archive memories, session-scoped knowledge

5. Conversation history      [DYNAMIC — grows each turn]
   Full message history with tool results

6. Working memory snapshot   [DYNAMIC — changes each turn]
   Current todo list, tracked files, decisions
```

The order is deliberate: static content first (maximizing prompt cache hits, Module 7), dynamic content last. The compositor also manages the context budget — if the total exceeds the window, it triggers auto-compaction on the conversation history (the most compressible component).

**SE parallel**: Template rendering with caching. A web framework renders pages from templates, partials, and dynamic data. Static partials are cached; dynamic data is injected per request. The prompt compositor does the same with prompt components.

### Layer 3: The Tool Execution Engine

When the LLM decides to call a tool, the runtime manages the entire execution lifecycle:

```
Tool Call Lifecycle:

1. PARSE: Extract tool name and arguments from LLM output
2. VALIDATE: Check arguments against the tool's JSON schema
3. AUTHORIZE: Check against permission policy (Module 15)
   → If human approval required, pause and wait for user
4. EXECUTE: Run the tool implementation
   → File operations run against the workspace
   → Shell commands run in the sandbox
   → External calls go through the egress proxy
5. CAPTURE: Collect stdout, stderr, return value, side effects
6. FORMAT: Transform result into a format suitable for the LLM
   → Truncate large outputs (Progressive Disclosure, Module 7)
   → Structure error messages for actionability
7. INJECT: Add the result to conversation history
8. LOG: Record the call for observability and replay
```

Each step is a middleware slot where the runtime can inject behavior: logging, caching (Action Caching, Module 14), rate limiting, or custom transformations.

**SE parallel**: This is exactly the middleware pipeline from Express/Koa/Django. Each step is a middleware function that can inspect, transform, or reject the request. The pipeline is configurable — different deployments can add different middleware without changing the core engine.

### Layer 4: The Sandbox Orchestrator

Code execution is the most dangerous tool capability (Module 6). The sandbox orchestrator manages isolated execution environments:

**Per-session sandboxes**: Each session gets an isolated environment — a container or VM with:
- A copy of the workspace (git worktree or rsync)
- Language runtimes and build tools
- Network restrictions (egress lockdown, Module 15)
- Resource limits (CPU, memory, time, disk)

**Workspace synchronization**: The sandbox's filesystem must stay in sync with the user's workspace. Edits the agent makes in the sandbox need to be reflected to the user. Files the user changes outside the agent need to be reflected in the sandbox. This is bidirectional sync — similar to how remote development environments (VS Code Remote, GitHub Codespaces) work.

**Lifecycle management**: Sandboxes are expensive resources. The orchestrator manages a pool (Adaptive Sandbox Fan-Out Controller, Module 16), pre-warming sandboxes for fast startup and terminating idle ones to reclaim resources.

### Layer 5: The Model Abstraction Layer

Production runtimes must work with multiple model providers and handle the differences transparently:

**Provider abstraction**: Different providers (Anthropic, OpenAI, Google) have different APIs, different tool-calling formats, different token counting methods, and different error codes. The model abstraction layer normalizes these into a unified interface so the rest of the runtime doesn't care which provider is being used.

**Model routing**: Based on task characteristics, the runtime selects the appropriate model (Router Agent, Module 8). The routing decision considers: task complexity, budget remaining, provider availability, and latency requirements.

**Fallback chains**: If the primary model is unavailable, the runtime falls back to alternatives (Failover-Aware Model Fallback, Module 14). Each fallback model has its own prompt variant — because a prompt optimized for Claude may not work well on GPT, and vice versa.

**SE parallel**: Database connection pooling with read replicas. The pool manages connections to multiple database instances, routes reads to replicas and writes to the primary, and fails over to a standby if the primary goes down. The model abstraction layer does the same for LLM API connections.

## Pattern: Virtual Machine Operator Agent

**What it does**: An agent that manages infrastructure — spinning up VMs, configuring environments, deploying code, managing cloud resources — using infrastructure-as-code tools as its "hands."

**SE parallel**: Ansible / Terraform operated by a human DevOps engineer. The agent replaces the human operator: it reads the desired state, determines what changes are needed, executes the infrastructure commands, and verifies the result.

**How it works**: The agent's tools are infrastructure operations: `create_vm(spec)`, `deploy_code(repo, branch, target)`, `configure_network(rules)`, `check_health(service)`. Its system prompt encodes operational runbooks. Given a task like "deploy the latest version of the auth service to staging," it:
1. Reads the deployment configuration
2. Creates or updates the target environment
3. Deploys the code
4. Runs health checks
5. Reports success or rolls back on failure

**Where it fits in the runtime**: The VM Operator is itself an agent that the runtime uses to manage its own infrastructure — creating sandboxes, scaling compute, managing development environments. It's the agent runtime using agents to manage itself.

**Trade-off**: Infrastructure operations are high-stakes — a misconfigured VM or a bad deployment can take down production. The VM Operator must operate with strict guardrails: require approval for production changes, use canary deployments (Module 14), and maintain rollback capability.

## Pattern: Subagent Compilation Checker

**What it does**: After a sub-agent (Module 9) produces code, a dedicated verification agent compiles, lints, and type-checks the output before returning it to the parent — catching errors that the generating agent missed.

**SE parallel**: Build verification / gated check-in. Code doesn't merge until the build passes. The compilation checker applies the same gate to sub-agent output: the code must compile, pass type-checking, and satisfy lint rules before it's accepted.

**How it works**: Sub-agent generates code → Compilation Checker receives the code → runs the compiler/type-checker/linter in the sandbox → if errors, returns them to the sub-agent for correction → loop until clean or budget exhausted → only clean code returns to the parent.

**Why a separate agent?** The generating agent might not have the full project context needed to verify compilation (it was spawned with minimal context for efficiency). The checker runs in the full project environment where compilation can be properly verified.

## The Runtime as a Product

The agent runtime is not just infrastructure — it's the product that developers interact with. Its design choices directly shape the developer experience:

**Extensibility model**: How do developers add custom tools? MCP (Module 6) provides a standard protocol, but the runtime must also support: local tool definitions, tool filtering by project, and tool lifecycle management (versioning, deprecation).

**Configuration hierarchy**: How do global settings, project settings, and session settings interact? The Layered Configuration Context pattern (Module 7) defines the precedence, but the runtime must implement it: reading configuration from multiple sources, merging with defined override rules, and making the effective configuration inspectable.

**Hooks and lifecycle events**: How do developers customize runtime behavior without modifying the runtime itself? Hook points (pre-tool-execution, post-generation, session-start, session-end) let developers inject custom logic — security checks, logging, notification, or custom validation.

**SE parallel**: This is framework design — Spring's dependency injection, Express's middleware, Django's signals. The runtime provides the lifecycle and extension points; developers plug in behavior. The quality of these extension points determines whether the runtime is a usable platform or a locked box.

## Key Takeaways

1. An agent runtime is an application server — it manages sessions, composes prompts, executes tools, orchestrates sandboxes, and abstracts model providers. Understanding this architecture is prerequisite to building or extending agent platforms.
2. Prompt composition is a layered caching problem — static components first for cache efficiency, dynamic components last. The compositor manages the context budget through auto-compaction.
3. The tool execution engine is a middleware pipeline — parse, validate, authorize, execute, capture, format, inject. Each slot is an extension point for custom behavior.
4. The sandbox orchestrator is container orchestration applied to code execution — isolation, resource limits, workspace sync, and pool management.
5. Virtual Machine Operator Agent and Subagent Compilation Checker represent the runtime using agents to manage its own infrastructure and quality — agents all the way down.

## Try This

Reverse-engineer an existing agent runtime:
1. Use Claude Code (or any coding agent with tool use) on a real project.
2. For a single task, map every observable event: What tools were called? In what order? How was the context composed? What permission checks occurred? How was the output formatted?
3. Draw the flow through the five layers described in this module: session manager → prompt compositor → tool execution engine → sandbox → model abstraction.
4. Identify: Which layers are visible to you as a user? Which are invisible? Where could you customize behavior (hooks, configuration, tools)?

## System Design Question

You're designing an agent runtime that must support: 100 concurrent sessions, 3 model providers (with fallback), per-project tool configurations, sandboxed code execution, and prompt caching. Design the architecture: How do you manage session state (in-memory, Redis, database)? How do you implement the model abstraction layer to handle provider differences? How do you manage the sandbox pool (pre-warming, scaling, cleanup)? What's your strategy for prompt composition that maximizes cache hit rate across sessions for the same project?
