# Module 20: Interaction Patterns

**Software engineering parallel**: User interface design for complex systems — the patterns that make powerful tools accessible: progressive disclosure, approval workflows, real-time feedback, interruption handling, and the controls that let users trust the system enough to let it work autonomously.

**Patterns covered**: Human-in-the-Loop Approval Framework, Spectrum of Control / Blended Initiative, Seamless Background-to-Foreground Handoff, Verbose Reasoning Transparency, Chain-of-Thought Monitoring & Interruption, Agent-Assisted Scaffolding, Proactive Trigger Vocabulary, Abstracted Code Representation for Review

---

## The Trust Problem

Every module so far has been about making agents capable. This module is about making agents *usable* — specifically, about the interface between the agent and the human who relies on it.

The core challenge is trust. An agent that can edit files, run commands, and create pull requests is powerful. It's also terrifying. A user who doesn't trust the agent will approve every action manually, defeating the purpose of automation. A user who trusts the agent blindly will miss the catastrophic mistake on turn 47. The interaction patterns in this module calibrate trust — giving users the right amount of visibility and control for the right situations.

## Control and Autonomy

### Human-in-the-Loop Approval Framework

**What it does**: Classifies agent actions by risk level and requires human approval for actions above a threshold — while letting low-risk actions proceed automatically.

**SE parallel**: PR review / approval gates. Not every code change needs a senior engineer's review. Formatting changes auto-merge; security-sensitive changes require two approvals. The approval framework applies the same tiered approach to agent actions.

**Implementation**:
```
Risk classification:

AUTO-APPROVE (no user interaction):
  - Read file, search code, list directory
  - Run read-only analysis commands
  - Generate plans, reasoning, explanations

NOTIFY (show user, proceed unless rejected):
  - Write file within project directory
  - Run test suite
  - Install dependencies from approved registries

REQUIRE APPROVAL (pause and wait):
  - Run arbitrary shell commands
  - Modify files outside project
  - Git push, create PR, deploy
  - Delete files, modify configuration

BLOCK (never allow):
  - Actions matching security policy deny rules
```

**UX design**: The approval prompt must show: what the agent wants to do, why (the reasoning that led to this action), and the expected impact. "Edit `/src/auth.py` lines 45-52: adding input validation for the email parameter. This fixes the issue identified in the failing test." — not just "Write to file? [y/n]".

**Trade-off**: Too many approvals create approval fatigue — the user starts hitting "yes" without reading, which is worse than no approvals at all. The risk classification must be calibrated so that approvals are rare enough to command attention but frequent enough to catch real mistakes.

### Spectrum of Control / Blended Initiative

**What it does**: Defines a continuum of autonomy levels that the user can move along — from fully manual (agent only suggests) to fully autonomous (agent acts independently) — with the user adjusting the level based on trust and context.

**SE parallel**: Self-driving levels L0-L5. L0 is fully manual driving. L2 is lane-keeping and adaptive cruise (human supervises). L5 is fully autonomous. The spectrum of control applies the same graduation to agents.

**The spectrum**:
| Level | Agent behavior | Human role | When to use |
|-------|---------------|------------|-------------|
| **Suggest** | Proposes actions, doesn't execute | Decides and executes | New agent, unfamiliar codebase |
| **Confirm** | Proposes and executes on approval | Reviews each action | Normal interactive use |
| **Autonomous with review** | Executes freely, presents result for review | Reviews the outcome | Trusted agent, routine tasks |
| **Fully autonomous** | Executes and commits/deploys | Monitors metrics | Background processing, CI/CD |

**Key insight**: The level should be adjustable *per task* and *per action type*, not globally. A user might run at "autonomous with review" for code edits but "confirm" for git operations — within the same session. Module 8 flagged the UX challenge of budget-driven model degradation; this pattern addresses it: when the budget forces a shift to cheaper models, the system should also shift toward more supervised autonomy levels, since cheaper models make more mistakes.

### Seamless Background-to-Foreground Handoff

**What it does**: Allows an agent to start work in the background and seamlessly bring the user into the loop when it needs input, hits an obstacle, or completes the task.

**SE parallel**: Async job → notification → UI. A CI build runs in the background. When it finishes (or fails), you get a notification. Clicking the notification takes you to the build results. Background-to-foreground handoff applies the same flow to agent sessions.

**How it works**:
1. Agent starts background task (e.g., "fix all lint errors in the project")
2. Agent works autonomously — reading files, making changes, running tests
3. If the agent needs human input (ambiguous requirement, risky action) → notification to user with full context → user responds → agent continues
4. When complete → notification with summary and diff → user reviews
5. User can "take over" at any point — switching from background to interactive mode

**Why it matters**: Not every task needs interactive supervision. Background execution frees the user to do other work. But the handoff must be seamless — the user who takes over should see exactly where the agent is, what it's done, and what decisions it's made, without re-reading the full conversation history.

## Visibility and Transparency

### Verbose Reasoning Transparency

**What it does**: Makes the agent's reasoning process visible to the user — showing not just what the agent does, but why it does it.

**SE parallel**: `--verbose` flag / debug mode. When you run a build with `--verbose`, you see every step: which files are compiled, which dependencies are resolved, why a specific optimization was chosen. Verbose reasoning shows the agent's thought process at a similar level of detail.

**Implementation levels**:
- **Minimal**: Show tool calls and results. The user sees "Read file X" and "Edit file Y."
- **Standard**: Show reasoning summaries. "I'm reading the test file to understand the expected behavior before modifying the implementation."
- **Verbose**: Show full chain-of-thought reasoning. Every intermediate thought, every consideration.

**UX guideline**: Default to standard. Let power users opt into verbose. Never hide tool calls — the user must always see what actions the agent is taking on their behalf. Hidden actions erode trust.

### Chain-of-Thought Monitoring & Interruption

**What it does**: Displays the agent's reasoning in real-time (streaming) and lets the user interrupt mid-thought or mid-action when they see the agent going in the wrong direction.

**SE parallel**: Kill signals / Ctrl+C. When you see a build doing something wrong, you hit Ctrl+C — you don't wait for it to finish and then undo the damage. CoT monitoring gives users the same power: see the agent's reasoning as it's generated and interrupt before the wrong action executes.

**How it works**: The agent's output streams to the user token by token. The user sees the reasoning forming in real-time. At any point, the user can:
- **Interrupt**: Stop the current generation. The agent receives a signal that the user intervened.
- **Redirect**: Provide new instructions that override the current direction. "Don't refactor that — just fix the null check."
- **Approve and accelerate**: "That's the right approach, proceed without showing me every step."

**Why streaming matters**: A non-streaming agent that takes 30 seconds to respond is a black box for 30 seconds. A streaming agent that shows reasoning in real-time gives the user 30 seconds of transparency — they can intervene at second 5 when they see the agent misunderstanding the task.

### Abstracted Code Representation for Review

**What it does**: Presents agent-generated code changes in a format optimized for human review — diffs, summaries, and annotations — rather than raw code output.

**SE parallel**: Diff views (GitHub PR diff, `git diff`). Developers don't review code by reading entire files — they review diffs that show exactly what changed. Abstracted representation applies the same principle: show the user what the agent changed, not the entire file.

**Implementation**: After the agent edits files, present:
1. A summary of changes ("Added input validation to the signup endpoint — 3 files modified")
2. A diff view showing exactly what changed (additions in green, deletions in red)
3. Annotations explaining why each change was made
4. Confidence indicators ("high confidence this is correct" vs. "I'm unsure about this edge case — please review carefully")

## Proactive Assistance

### Agent-Assisted Scaffolding

**What it does**: The agent generates project structure, boilerplate, and configuration based on high-level requirements — handling the tedious setup so the developer can focus on business logic.

**SE parallel**: `create-react-app` / cookiecutter / `rails new`. Scaffolding tools generate project skeletons. Agent-assisted scaffolding goes further: it asks questions about requirements ("Do you need authentication? What database?"), generates a customized skeleton, and explains the architectural decisions it made.

**When to use it**: Project kickoffs, adding new modules to existing projects, configuring complex toolchains. The scaffolding agent handles the decisions that have well-established best practices, flagging decisions that require human judgment.

### Proactive Trigger Vocabulary

**What it does**: Defines a vocabulary of triggers that users can use to proactively invoke agent capabilities — commands, keywords, or conventions that activate specific behaviors.

**SE parallel**: Webhooks / cron expressions. Proactive triggers are the user-facing equivalent of webhook triggers (Module 18) — but initiated through natural language or structured commands rather than API calls.

**Examples**: `/review` triggers a code review. `/fix` triggers a bug-fix investigation. `/explain` triggers a code explanation. `@agent` in a PR comment triggers the agent to respond. The vocabulary should be discoverable (autocomplete, help commands), memorable, and extensible.

## Key Takeaways

1. Human-in-the-Loop Approval with risk-tiered classification is the baseline — auto-approve reads, require approval for destructive actions, block prohibited actions. Calibrate to avoid approval fatigue.
2. Spectrum of Control lets users adjust autonomy per task and per action type — from fully manual to fully autonomous. Shift toward more supervision when using cheaper models.
3. Streaming + Interruption gives users real-time visibility and the power to redirect the agent mid-reasoning. Non-streaming agents are black boxes that erode trust.
4. Abstracted Code Representation (diffs + summaries + annotations) makes agent output reviewable. Users should never have to read full files to understand what changed.
5. Background-to-Foreground Handoff enables autonomous work with seamless re-engagement — the agent works alone until it needs help, then brings the user in with full context.

## Try This

Implement a risk-tiered approval system:
1. Define 5 tools: `read_file` (low risk), `search_code` (low risk), `edit_file` (medium risk), `run_bash` (high risk), `git_push` (high risk).
2. Implement the approval logic: low risk auto-approves, medium risk shows the action and waits 3 seconds (proceed unless interrupted), high risk requires explicit approval.
3. Run a task that uses all 5 tools. Observe: Does the approval flow feel right? Is the pace natural? Where does the user want more or less control?
4. Adjust the risk levels based on experience. Does `edit_file` within the project feel low-risk enough to auto-approve after a few sessions?

## System Design Question

You're designing the UX for a coding agent that operates both interactively (IDE integration) and in the background (CI pipeline). Design the interaction model: How does the user set the autonomy level (Spectrum of Control)? How do background agents surface issues that need human input (Background-to-Foreground Handoff)? How do you present multi-file changes for review (Abstracted Representation)? How do you handle the case where the user is offline and the background agent needs a decision?
