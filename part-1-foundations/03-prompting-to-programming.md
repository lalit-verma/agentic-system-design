# Module 3: From Prompting to Programming

**Software engineering parallel**: The evolution from shell one-liners to structured programming — you start with ad-hoc commands, then develop functions, contracts, error handling, and composability.

**Patterns covered**: None (foundational module — establishes prompt engineering as a programming discipline, bridging to agent design in Part 2)

---

## The Mindset Shift

Most people encounter LLMs as chatbots — you type a question, get an answer. That's the equivalent of typing SQL directly into a database console. It works, but it's not software engineering.

This module reframes prompting as programming. The prompt is your source code. The LLM is your runtime. The output is your program's return value. And like any program, the quality of your output depends on the quality of your code — its structure, specificity, error handling, and composability.

By the end of this module, you'll see prompts as programs — which is exactly what they become inside an agent.

## The Anatomy of a Prompt-as-Program

An LLM API call has a structured format. Here's the architecture:

```
API Request:
├── model: "claude-sonnet-4-6"          # Runtime selection
├── max_tokens: 4096                      # Output budget
├── temperature: 0.2                      # Determinism control
├── system: "You are a code reviewer..." # System prompt (the "main" function)
└── messages:                             # Conversation history (call stack)
    ├── {role: "user", content: "..."}    # Input
    ├── {role: "assistant", content: "..."}# Prior output
    └── {role: "user", content: "..."}    # Current input
```

Each component maps to a programming concept:

### The System Prompt = Your Program's Main Function

The system prompt sets the model's persona, constraints, output format, and behavioral rules. It runs "first" in every interaction — the model treats it as the highest-authority instruction. Everything else is data flowing through this function.

**SE parallel**: This is the `main()` function or the application's bootstrap configuration. It defines the runtime behavior: what the program does, what it doesn't do, how it formats output, what constraints it respects. Change the system prompt and you change the program's behavior entirely — same codebase (model), different application.

A well-structured system prompt contains:

1. **Role definition** — who the model is (sets the domain and tone)
2. **Behavioral constraints** — what it must/must not do (the contract)
3. **Output format specification** — how responses should be structured (the schema)
4. **Examples** — concrete input/output pairs (the test cases)
5. **Edge case handling** — what to do when uncertain or when input is ambiguous (error handling)

This isn't just good practice — it has economic implications from Module 2. The system prompt is the ideal candidate for prompt caching: it's static across all calls in a session (and often across sessions), so it hits the cache and gets processed at 90% discount. This is why it goes first in the message structure.

### Messages = Your Call Stack

The messages array is the conversation history. Each user message is an input; each assistant message is a prior return value. The model sees this entire history on every call — it's the "call stack" that provides context for the current execution.

**SE parallel**: This is event sourcing applied to a conversation. The current state isn't stored separately — it's reconstructed by replaying all prior events (messages). This has the same trade-offs as event sourcing: you get a complete audit trail and can "replay" to any point, but the log grows linearly and processing cost grows with it (as Module 2 explained).

### Parameters = Compiler Flags

Temperature, max_tokens, top-p — these are the compiler flags or runtime configuration of your program. They don't change what the program does logically, but they change how it executes. Low temperature for deterministic output (like `-O2` optimization giving consistent results), high temperature for exploratory output (like fuzzing with random seeds).

## Prompt Engineering Techniques as Programming Patterns

### Zero-Shot: The Function Call

A zero-shot prompt gives the model a task with no examples. You're relying entirely on the model's parametric knowledge.

```
Classify this error message as one of: [timeout, auth_failure, rate_limit, unknown]

Error: "Connection refused after 30s waiting for response from upstream"
```

**SE parallel**: Calling a well-documented library function for the first time, trusting the API contract. It works when the task is within the model's training distribution — just as a library call works when you use it as documented.

**When it fails**: Ambiguous tasks, domain-specific formats, anything that requires conventions the model hasn't seen enough of in training.

### Few-Shot: Programming by Example

Few-shot prompting includes input/output examples before the actual task. This is the single most powerful technique for steering model behavior without fine-tuning.

```
Convert these error logs to structured JSON.

Input: "2024-03-15 ERROR [auth] Token expired for user_id=9281"
Output: {"timestamp": "2024-03-15", "level": "ERROR", "service": "auth", "message": "Token expired", "user_id": "9281"}

Input: "2024-03-15 WARN [cache] Miss rate above threshold, pool=redis-main"
Output: {"timestamp": "2024-03-15", "level": "WARN", "service": "cache", "message": "Miss rate above threshold", "pool": "redis-main"}

Input: "2024-03-16 ERROR [db] Deadlock detected on table=orders, txn_id=8843"
Output:
```

The model infers the pattern from examples and applies it to the new input. The examples function as a specification — they define the mapping more precisely than any verbal description could.

**SE parallel**: This is test-driven development applied to prompts. Your examples are simultaneously the specification and the test cases. If the model produces output that doesn't match the pattern in your examples, you know the prompt needs revision — just like a failing test tells you the code needs fixing.

**Trade-off**: Each example consumes context window tokens and adds to your input cost. Three good examples are almost always better than ten mediocre ones. This is the tension between specification completeness and context budget — a preview of the Context-Minimization pattern from Module 7.

### Chain-of-Thought: Show Your Work

Asking the model to "think step by step" before answering significantly improves accuracy on reasoning tasks. This technique forces the model to generate intermediate reasoning tokens before the final answer, effectively giving it "scratch space."

```
Determine if this database migration is safe to run without downtime.
Think through each change step by step before giving your verdict.

Migration:
  ALTER TABLE orders ADD COLUMN status VARCHAR(50) DEFAULT 'pending';
  CREATE INDEX idx_orders_status ON orders(status);
```

The model will reason through: adding a column with a default is safe in most databases (but not all — Postgres before 11 rewrites the table), creating an index is potentially blocking depending on the engine, etc.

**SE parallel**: This is debug logging or trace logging. When a function produces an unexpected result, you add logging to see the intermediate steps. Chain-of-thought is adding `--verbose` to your LLM call. The output is longer (more expensive, per Module 2) but you can observe the reasoning path, which is essential for debugging and trust.

This is a preview of the Chain-of-Thought pattern in Module 5, and it directly relates to extended thinking (Module 2) — the difference being that chain-of-thought in the visible output is inspectable, while extended thinking happens in hidden tokens.

### Structured Output: Schema Enforcement

Instead of hoping the model returns well-formatted output, you can constrain it to a specific schema. Most APIs support this natively:

```
Response format: JSON matching this schema:
{
  "verdict": "safe" | "unsafe" | "needs_review",
  "risks": [{"description": string, "severity": "low" | "medium" | "high"}],
  "recommendation": string
}
```

Some APIs go further — they enforce the schema at the token-generation level through constrained decoding, guaranteeing valid JSON that matches your schema. This eliminates an entire class of errors.

**SE parallel**: This is protobuf or JSON Schema for API contracts. You don't trust the caller (or the model) to produce valid output by convention alone — you enforce it structurally. This is the foundation of the Structured Output Specification pattern in Module 14, where reliability at scale depends on never getting a malformed response.

**Trade-off**: Schema enforcement can slightly reduce output quality because the model can't "think" in its natural format before producing structured output. The mitigation is to allow a "reasoning" field in your schema — let the model think, then extract the structured result. This costs more tokens but gets you both structure and quality.

## The Prompt as a Deployment Artifact

In production agentic systems, prompts are not casual text — they're deployment artifacts that need the same rigor as code.

### Version Control

System prompts should live in version control alongside your application code. A change to the system prompt changes your application's behavior as surely as a code change. Diffing, reviewing, and rolling back prompts should be as natural as doing the same for source code.

**SE parallel**: Configuration-as-code. Terraform files, Kubernetes manifests, feature flag configurations — anything that affects runtime behavior belongs in version control.

### Prompt Composition

Real-world prompts are assembled from components, not written as monolithic blocks. A coding agent's prompt might be composed from:

```
final_prompt = system_base            # Base persona and rules
  + tool_definitions                  # Available tools and their schemas
  + project_context                   # CLAUDE.md, repo structure
  + file_contents                     # Currently relevant files
  + conversation_history              # Prior turns
  + current_task                      # What the user just asked
```

Each component can be independently maintained, tested, and swapped. The composition order matters — both for logical clarity and for prompt caching (static components first, dynamic components last, as discussed in Module 2).

**SE parallel**: This is dependency injection for prompts. Each component is a dependency injected at runtime based on the current context. The composition root (your agent framework) assembles the final prompt from these components. This becomes the Layered Configuration Context and Dynamic Context Injection patterns in Module 7.

### Prompt Testing

How do you know your prompt works correctly? You need evaluation:

1. **Unit-level**: Does the prompt produce the right output for known inputs? Run it against a test suite of input/expected-output pairs.
2. **Regression-level**: After a prompt change, does it still pass all previous test cases?
3. **Behavioral-level**: Does the prompt handle edge cases — ambiguous input, adversarial input, empty input?

**SE parallel**: This is literally a test suite. Unit tests (known inputs), regression tests (don't break existing behavior), and edge-case tests (boundary conditions). The difference is that LLM outputs are nondeterministic, so "passing" means statistical — you might run each test case 5 times and require 4/5 correct. This introduces the concept of **evals** (evaluations), which become a major topic in Modules 12-13 and the backbone of Part 6.

## From Prompt to Agent: The Bridge

Here's where everything connects. An agent is a program that:

1. Takes a task (user input)
2. Decides what to do (reasoning — Module 5)
3. Takes action (tool use — Module 6)
4. Observes the result (context injection)
5. Repeats until the task is done (loop)

Each step involves an LLM call, and each call is structured using the principles in this module — system prompts that define behavior, structured outputs that enable reliable parsing, few-shot examples that steer toward correct patterns, and chain-of-thought that enables complex reasoning.

The difference between "prompting" and "agent design" is the difference between writing a function and designing a system. A single prompt is a function. An agent is a system composed of many prompts, orchestrated by control flow, with state managed externally, tools providing capabilities, and feedback loops ensuring quality.

```
Agent Loop (pseudocode):

state = initial_context
while not task_complete(state):
    prompt = compose_prompt(system_rules, state, available_tools)
    response = llm_call(prompt, temperature=0.2, response_format=ActionSchema)

    if response.action == "use_tool":
        result = execute_tool(response.tool_name, response.tool_args)
        state = update_state(state, result)
    elif response.action == "respond":
        return response.content
    elif response.action == "think":
        state = update_state(state, response.reasoning)
```

This is the skeleton you'll flesh out across Part 2. Every module from here forward builds on this loop — adding reasoning strategies (Module 5), tool integration (Module 6), memory management (Module 7), and eventually multi-agent coordination (Part 3).

## Key Takeaways

1. A prompt is a program: system prompt is main(), messages are the call stack, parameters are compiler flags. Treat prompts with the same engineering rigor as code.
2. Few-shot examples are the most reliable steering mechanism — they function as both specification and test cases.
3. Chain-of-thought prompting trades tokens for accuracy. It's the `--verbose` flag for LLM reasoning.
4. Structured output schemas eliminate parsing errors and enable reliable automation. Enforce schemas structurally, not by convention.
5. An agent is a loop of prompted LLM calls with tool use, state management, and control flow — turning prompts from one-shot functions into sustained programs.

## Try This

Build a prompt-as-program for a concrete task: take any API error log format you're familiar with, and write a system prompt that converts unstructured log lines into structured JSON. Include:
- A system prompt with role, constraints, and output schema
- Three few-shot examples covering different error types
- Edge case instructions (what to do with malformed log lines)

Test it against 10 real or realistic log lines. Track: how many parse correctly on first try, which fail, and why. Iterate on the prompt to fix failures — this is the prompt development loop you'll use constantly.

## System Design Question

You're building an agent that reviews pull requests. The agent needs to: read the diff, check for common issues (security, performance, style), and produce a structured review with line-specific comments. Design the prompt architecture — what goes in the system prompt, what's injected dynamically, how you'd structure the output schema, and how you'd test that the agent produces useful reviews rather than generic boilerplate. Consider the prompt caching implications from Module 2 in your design.
