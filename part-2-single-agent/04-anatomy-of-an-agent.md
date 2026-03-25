# Module 4: Anatomy of an Agent

**Software engineering parallel**: A web application framework — it has a request-response loop, middleware pipeline, route handlers (tools), session management (memory), and configuration (system prompt).

**Patterns covered**: None formally (architectural module — defines the subsystems that Modules 5-7 fill with named patterns)

---

## What Makes Something an "Agent"

Module 3 ended with a pseudocode agent loop. Now we need to turn that sketch into an architecture. But first, a definition.

An **agent** is a system where an LLM makes decisions about control flow. That's it. If your code calls an LLM and uses the response to decide what to do next — which tool to call, whether to continue, what to investigate — you have an agent. If your code calls an LLM in a fixed pipeline with predetermined steps, you have a workflow with LLM steps, but not an agent.

**SE parallel**: The distinction between a static batch script and a dynamic application server. A batch script runs steps 1-2-3-4 in order. An application server receives a request, inspects it, routes it to the appropriate handler, and the handler may call other services, retry, redirect — the execution path is determined at runtime. Agents are application servers. Workflows are batch scripts.

This distinction matters because agents inherit all the challenges of dynamic systems: they can loop infinitely, make wrong decisions, take expensive detours, and behave unpredictably. Every pattern in this course exists to manage those challenges.

## The Agent Runtime Architecture

Here's the complete architecture of a single-agent system. Every production agent — Claude Code, Cursor, Devin, GitHub Copilot — implements some variant of this:

```
┌─────────────────────────────────────────────────┐
│                  Agent Runtime                    │
│                                                   │
│  ┌──────────┐   ┌───────────┐   ┌────────────┐  │
│  │ System    │   │ Reasoning │   │ Tool       │  │
│  │ Prompt    │──▶│ Engine    │──▶│ Executor   │  │
│  │ (Config)  │   │ (LLM)     │   │ (Dispatch) │  │
│  └──────────┘   └─────┬─────┘   └──────┬─────┘  │
│                       │                  │        │
│                       ▼                  ▼        │
│              ┌────────────────┐  ┌────────────┐  │
│              │ State Manager  │  │ Tool       │  │
│              │ (Memory)       │  │ Registry   │  │
│              └────────────────┘  └────────────┘  │
│                       │                           │
│                       ▼                           │
│              ┌────────────────┐                   │
│              │ Stop Condition │                   │
│              │ Evaluator      │                   │
│              └────────────────┘                   │
└─────────────────────────────────────────────────┘
```

Six subsystems. Let's examine each.

## Subsystem 1: The System Prompt (Configuration)

We covered system prompts in Module 3 as a programming construct. In an agent, the system prompt takes on an expanded role — it's the agent's operating system configuration. Beyond persona and output format, it defines:

- **Available tools and their contracts**: What the agent can do, described in natural language and JSON schema.
- **Behavioral guardrails**: What the agent must never do (delete production data, commit to main without review).
- **Decision heuristics**: When to use which tool, when to ask the user vs. proceed autonomously.
- **Identity and accumulated knowledge**: Project-specific context, like a CLAUDE.md file that tells the agent about the codebase.

**SE parallel**: This is the application's configuration bundle — `application.yml` + route definitions + middleware registration + security policies, all loaded at startup. The system prompt is bootstrapped once and stays (mostly) stable across the agent's lifetime.

The system prompt is also the anchor for prompt caching (Module 2). Because it's the first thing in every request and remains identical across turns, it gets cached at 90% discount. Anything you can move into the system prompt rather than injecting dynamically saves money and improves cache hit rates.

## Subsystem 2: The Reasoning Engine (LLM)

The LLM is the agent's decision-maker. Each turn, it receives the full context (system prompt + conversation history + tool results) and decides one of three things:

1. **Use a tool** — call a specific tool with specific arguments
2. **Respond to the user** — return a final answer or ask a clarifying question
3. **Think** — generate intermediate reasoning before acting (chain-of-thought)

This is the "brain" of the agent, and its quality depends entirely on the model's capability, the reasoning strategy used, and the quality of context provided. Module 5 covers reasoning patterns in depth — different strategies for how the LLM makes these decisions.

**SE parallel**: The routing layer in a request pipeline. Like an API gateway that inspects the request and routes to the appropriate handler, the LLM inspects the context and routes to the appropriate action. The difference is that routing logic is learned (from training data and the system prompt) rather than hardcoded.

## Subsystem 3: The Tool Registry

An agent without tools is a chatbot. Tools are what give agents the ability to act — read files, write code, query databases, make API calls, run tests.

A **tool** is a function with:
- A **name** (e.g., `read_file`, `run_bash`, `web_search`)
- A **description** in natural language (so the LLM understands when to use it)
- A **parameter schema** (JSON Schema defining expected inputs)
- An **implementation** (the actual code that executes)

```
Tool Definition (pseudocode):

tool "read_file":
  description: "Read contents of a file at the given path"
  parameters:
    path: string (required) — "Absolute path to the file"
    offset: integer (optional) — "Line number to start reading from"
    limit: integer (optional) — "Maximum number of lines to read"
  implementation: (path, offset, limit) => filesystem.read(path, offset, limit)
```

The tool registry is the collection of all available tools. The LLM sees tool descriptions and schemas in its context (typically as part of the system prompt or a special API parameter) and decides which tool to call based on the current task.

**SE parallel**: This is a service registry combined with API documentation. Each tool is a microservice endpoint: it has a contract (schema), documentation (description), and implementation. The LLM discovers available tools the same way a developer discovers available APIs — by reading the docs. This architecture enables the Progressive Tool Discovery and LLM-Friendly API Design patterns (Module 6).

### The Tool Execution Cycle

When the LLM decides to use a tool, the following happens:

1. **LLM outputs a structured tool call**: `{tool: "read_file", args: {path: "/src/main.py"}}`
2. **Runtime validates the call**: Does this tool exist? Are the arguments valid against the schema?
3. **Permission check**: Is the agent authorized to use this tool? Does the user need to approve?
4. **Execution**: The tool runs and produces a result.
5. **Result injection**: The result is added to the conversation history as a tool result message.
6. **Next LLM call**: The LLM sees the result and decides what to do next.

This is one "turn" of the agent loop. A typical agent session involves dozens of these turns.

**SE parallel**: This is the middleware pipeline pattern. Request comes in → validation middleware → authorization middleware → handler execution → response formatting → back to the client. Each step can reject the request or transform it.

## Subsystem 4: The State Manager (Memory)

The LLM is stateless (Module 1). The state manager is everything the agent builds around it to create the illusion of continuity. It manages:

- **Conversation history**: The full sequence of messages (user, assistant, tool results). This is the "source of truth" that gets sent to the LLM on every call.
- **Working memory**: Short-term structured state — the current task list, files being tracked, decisions made. Often implemented as a scratchpad the agent reads and updates.
- **Long-term memory**: Information that persists across sessions — user preferences, project facts, accumulated learnings. Stored externally (filesystem, database) and loaded selectively.

**SE parallel**: This maps directly to the storage hierarchy in any stateful application. Conversation history is the request log. Working memory is the in-process cache (Redis, local state). Long-term memory is the database. Each tier has different capacity, latency, and cost characteristics — exactly the trade-offs we'll formalize as the Hierarchical Memory pattern in Module 7.

The state manager is also where you feel the economics from Module 2 most directly. Every piece of state you keep in the conversation history gets re-processed on every turn (and billed accordingly). The tension between "keep everything for context" and "minimize tokens for cost and quality" drives an entire family of context management patterns.

## Subsystem 5: The Tool Registry's Sibling — The Permission Model

In traditional software, the application runs with whatever permissions you give it at deploy time. Agents are different: they make their own decisions about what to do, so the permission model must constrain those decisions at runtime.

Three common permission approaches:

1. **Allow-list**: The agent can only use explicitly permitted tools. Safe but limits capability.
2. **Human-in-the-loop**: Certain actions (write to disk, run commands, make API calls) require user approval before execution. This is how Claude Code works — you see the proposed action and approve or deny it.
3. **Policy-based**: Rules define what's allowed based on context: "read any file, but only write to files in the project directory. Run tests freely, but require approval for `git push`."

**SE parallel**: OAuth scopes meet runtime authorization. The tool registry defines capabilities (like API scopes), and the permission model acts as the authorization layer that checks each request against the policy. This becomes the Sandboxed Tool Authorization pattern in Module 15.

## Subsystem 6: Stop Conditions

An agent loop needs to know when to stop. Without explicit stop conditions, you get infinite loops, runaway costs, and an agent that keeps "trying" long after it should have given up.

Common stop conditions:

- **Task completion**: The LLM decides the task is done and returns a final response.
- **Token budget**: Total input + output tokens across the session exceed a threshold.
- **Turn limit**: The agent has taken N steps without completing the task.
- **Error threshold**: Too many consecutive tool failures.
- **Time limit**: Wall clock time exceeded.
- **User interruption**: The user cancels or redirects.

**SE parallel**: Circuit breakers and timeout policies. Every distributed system needs them — an HTTP client without a timeout is a bug. An agent without a token budget is a billing incident.

The design question is what happens when a stop condition triggers. Options: return the best result so far, ask the user for guidance, save state and offer to resume later. The right choice depends on the use case — an interactive coding agent should ask the user, while a batch processing agent should save state and move on.

## The Complete Loop, Revisited

Module 3's pseudocode was the skeleton. Here's the full architecture:

```
Agent Session:

1. INITIALIZE
   - Load system prompt (persona, tools, rules, project context)
   - Initialize state manager (load memory, create working state)
   - Register tool handlers

2. LOOP
   a. COMPOSE context
      - System prompt (static, cached)
      - Conversation history (growing, expensive)
      - Working memory snapshot (dynamic)
      - Current tool results (if any)

   b. CALL LLM with composed context
      - Model selection (frontier vs. fast based on task phase)
      - Temperature selection (low for tool calls, moderate for planning)
      - Response format (structured output schema for tool calls)

   c. PARSE response
      - Tool call → validate, authorize, execute, inject result, continue loop
      - Final answer → return to user, exit loop
      - Thinking → append to history, continue loop

   d. CHECK stop conditions
      - Budget exceeded? Turn limit reached? Error threshold?
      - If triggered: graceful shutdown with best available result

3. CLEANUP
   - Persist relevant state to long-term memory
   - Log session metrics (tokens, cost, turns, tools used)
```

Every subsystem is a plug point where patterns can be applied. The reasoning engine accepts different reasoning strategies (Module 5). The tool executor accepts different tool architectures (Module 6). The state manager accepts different memory strategies (Module 7). The architecture is the skeleton; the patterns are the muscles.

## Agents vs. Workflows vs. Pipelines

A quick taxonomy, because these terms get confused:

| | Pipeline | Workflow | Agent |
|---|---|---|---|
| **Control flow** | Fixed sequence | Conditional branches | LLM-decided |
| **Steps** | Predetermined | Predetermined with forks | Discovered at runtime |
| **Predictability** | Fully deterministic | Mostly deterministic | Nondeterministic |
| **Cost** | Cheapest (minimal LLM) | Moderate | Expensive (many LLM calls) |
| **When to use** | ETL, batch processing | Multi-step with known paths | Open-ended, exploratory tasks |

**SE parallel**: Pipeline = shell script. Workflow = Apache Airflow DAG. Agent = human developer at a terminal. Most production systems use a mix — agents for the open-ended parts, workflows for the well-understood parts. Knowing when to use which is a key architectural skill.

A common anti-pattern is using agents for tasks that should be workflows. If you know the steps in advance — "extract data, validate it, transform it, load it" — don't pay for an agent to rediscover those steps every time. Use deterministic code. Agents earn their cost only when the execution path cannot be predetermined.

## Key Takeaways

1. An agent is defined by LLM-controlled control flow — the model decides what to do next. Everything else is a workflow or pipeline.
2. The six subsystems — system prompt, reasoning engine, tool registry, tool executor, state manager, stop conditions — compose every agent architecture from Claude Code to Devin.
3. Tools are functions with schemas and descriptions. The LLM selects and invokes them based on natural language understanding of the task and tool documentation.
4. The permission model constrains agent autonomy at runtime — allow-lists, human-in-the-loop, or policy-based authorization.
5. Stop conditions are mandatory. An agent without a budget is a runaway process.

## Try This

Using any LLM API with tool use support (Claude, GPT, Gemini), build a minimal agent loop:
1. Define two tools: `read_file(path)` and `list_directory(path)`.
2. Write a system prompt that instructs the agent to explore a directory and summarize what it finds.
3. Implement the loop: call the LLM, parse tool calls, execute them, feed results back, repeat until the LLM returns a final answer.
4. Add a turn limit of 10 and observe: does the agent finish within the budget? What happens when it hits the limit?

This exercise makes the architecture concrete — you'll see exactly how the tool cycle, state accumulation, and stop conditions work.

## System Design Question

You're designing a coding agent that can read files, edit files, and run tests. A user asks it to "add input validation to the signup endpoint." Trace through the agent loop: what does the system prompt need to contain? What sequence of tool calls would you expect? Where might the agent loop excessively, and what stop conditions would you set? How much context accumulates by the time the agent is done, and what does that cost at $3/$15 per million tokens?
