# CCA-F Phase 0 — Foundations Refresh

> **Purpose:** Calibration, not learning. Confirm your foundation is solid before P1 builds on it.
> **Duration target:** 2 days (10 hrs/day budget assumed).
> **Advancement gate:** 5/6 on end-of-phase quiz, plus echo agent passes all 3 acceptance tests.

---

## Day plan

| Day | Block | Activity |
|---|---|---|
| 1 | morning (3h) | Read concept refresh below. For each concept, write a 1-sentence definition from memory, then compare against the source. |
| 1 | midday (3h) | Build `echo_agent.py` from spec. Run 3 acceptance tests. |
| 1 | afternoon (1.5h) | Break-it exercise: introduce 3 intentional anti-patterns (see below), observe what fails. |
| 1 | evening (1h) | Import Mochi deck. Run first review pass. |
| 2 | morning (2h) | Re-read concept refresh. Cover answers; quiz yourself before checking. |
| 2 | midday (2h) | Take end-of-phase quiz. Score honestly. |
| 2 | afternoon (2h) | Friday log post draft: one concept that clicked, one trap fallen into, one thing built. |
| 2 | evening (1h) | Mochi review + advance-or-reset decision. |

---

## Concept refresh (7 must-own concepts)

| # | Concept | Core fact | Anti-pattern |
|---|---|---|---|
| 1 | **Agentic loop lifecycle** | `stop_reason` drives the loop: `"tool_use"` continues, `"end_turn"` terminates. | Parsing text for "I'm done" or "final answer"; using assistant text presence as completion. |
| 2 | **Tool result handoff** | After each `tool_use`, append the assistant turn AND a `role=user` turn containing `tool_result` blocks (one per tool call) before the next API call. | Skipping the assistant turn, or batching tool calls across iterations instead of within one response. |
| 3 | **Iteration cap as backstop** | Caps exist to prevent runaway costs, not to terminate normal loops. Hitting the cap signals a bug. | Designing the loop around a cap; raising the cap when it trips instead of investigating. |
| 4 | **Tool description quality** | Tool descriptions are the **primary** mechanism the model uses to select among tools. They should specify purpose, input format, examples, edge cases, and when to use vs alternatives. | One-line vague descriptions like "Get customer info" that overlap with similar tools. |
| 5 | **Prompt chaining vs parallelization** | **Chaining** = sequential, each step depends on the prior. **Parallelization** = independent work, results aggregated. A per-file pass + an integration pass is chaining (the integration step depends on the per-file outputs). | Calling per-file analysis "parallel" when downstream steps require all results first. |
| 6 | **Built-in tool selection (Grep / Glob / Read / Edit)** | `Grep` = content search. `Glob` = filename/path patterns. `Read` = full file. `Edit` = targeted edit by unique anchor; fall back to `Read`+`Write` when anchor isn't unique. | Using `Glob` to find import statements (it only matches paths). Using `Edit` when the anchor text appears 3 times in the file. |
| 7 | **Verbose tool output trimming** | Tools that return 40+ fields when 4 are needed will saturate context across a session. Trim at the source (the tool wrapper) or via a `PostToolUse` hook before the result enters context. | Increasing `max_tokens` (output budget, not input). Switching models to "fix" context bloat. |

---

## Echo agent v0 — build spec

### Functional requirements

- Single Python file, single tool, single agentic loop.
- Tool: `echo(text: str) -> str` that returns `[ECHO: {text}]`.
- Loop control: `stop_reason == "end_turn"` terminates; `"tool_use"` continues; any other value raises.
- Backstop: `max_iterations = 10`. Tripping it raises `RuntimeError`.

### [Acceptance tests](./001_echo_agent.py)

Run each test, inspect stderr for the iteration trace, confirm behavior:

| # | Input | Expected behavior |
|---|---|---|
| 1 | `"Please echo 'hello world' back to me."` | 1 tool call to `echo`, then `end_turn` with confirmation text. Iteration count: 2. |
| 2 | `"What is 2 plus 2?"` | Zero tool calls; immediate `end_turn` with "4" or similar. Iteration count: 1. |
| 3 | `"Echo 'first' and then echo 'second' separately."` | Either 1 response with 2 parallel `tool_use` blocks, OR 2 sequential iterations. Both are valid; observe which the model chose and why. |

### Break-it exercises (Day 1 afternoon, 1.5h)

Introduce each anti-pattern below, run the agent, observe the failure mode:

1. **Replace `stop_reason` check with iteration cap.** [Two-part exercise](./002_echo_agent.py). The point is to see how the safety rail interacts with the anti-pattern, not just the anti-pattern alone.
    - **1a.** Change ONLY the `end_turn` check to `if iteration == 5: break`. Leave the final `raise RuntimeError(...)` intact. Run test 2 (`"What is 2 plus 2?"`).
        - **Predicted failure:** The model returns `end_turn` on iteration 0. Your broken loop doesn't terminate. Falls through to the `raise` and crashes with `RuntimeError("Unexpected stop_reason: 'end_turn'")`.
        - **Lesson:** A defensive rail that raises on any unhandled `stop_reason` is what makes the anti-pattern *visible*. Real codebases often lack this rail.
    - **1b.** Now ALSO replace the **in-loop** rail (`raise RuntimeError("Unexpected stop_reason: ...")`, the one inside the `for` loop) with `pass`. Leave the post-loop backstop (`raise RuntimeError("Hit max_iterations backstop ...")`) intact. Re-run test 2.
        - **Predicted failure:** `end_turn` no longer crashes; it falls through `pass`. The loop makes 6 API calls (iterations 0 through 5, because the API call sits at the top of the loop body), each logging `stop_reason: end_turn`, then `break` fires on iteration 5 and execution lands on the post-loop backstop, crashing with `RuntimeError("Hit max_iterations backstop ...")`.
        - **Lesson:** Removing the in-loop rail just hands the runaway to the second rail. The agent has two independent rails; one edit cannot make it fail silently. To see a truly silent `None` return you would have to remove the backstop too.
    - **1c (optional).** Also delete the post-loop backstop. Re-run test 2.
        - **Predicted failure:** 6 wasted API calls, `break` on iteration 5, function falls off its end and returns `None`. No exception, no result.
        - **Lesson:** This is the anti-pattern in its fully silent form. It only happens when nothing is left to catch the runaway.
    Revert both edits before exercise 2.
  > More details on the [stop reason control flow](./stop_reason_controlflow.md)

---

2. **Skip the assistant turn append.** Delete `messages.append({"role": "assistant", "content": response.content})`. Observe the API error.
3. **Force `max_tokens` mid-tool-call.** Change `max_tokens=1024` to `max_tokens=20`. Run test 1. Observe `stop_reason` becomes `"max_tokens"` and the loop correctly raises (your `RuntimeError`).

After each: revert. Write 1 sentence in your log explaining the failure mode.

---

## End-of-phase quiz (6 questions, advance at 5/6)

> Take this closed-book. Score yourself before reading rationales.

---

### Q1 (Domain 1.1)

You're building an agentic loop. After each `messages.create()` call, what is the most reliable signal to determine whether to continue the loop or terminate?

- **A)** Check if the response contains any text content; if yes, the model is done and you should terminate.
- **B)** Inspect `stop_reason`: continue when it equals `"tool_use"`, terminate when it equals `"end_turn"`.
- **C)** Set a fixed `max_iterations` of 10 and exit when the counter reaches it.
- **D)** Parse the response text for phrases like "I'm done," "final answer," or "in conclusion."

<details>
<summary>Answer</summary>

**Correct: B**

- **A wrong:** Tool-use responses often contain reasoning text alongside the tool call. Text presence does not indicate completion.
- **C wrong:** Iteration caps are backstops against runaway loops, not primary stop signals. Designing around the cap is the canonical anti-pattern.
- **D wrong:** Parsing natural language for completion is brittle and explicitly called out as an anti-pattern in Domain 1.1.

</details>

---

### Q2 (Domain 1.1)

Your agentic loop terminates when `iteration_count == max_iterations` (set to 20). In code review, a colleague flags this as the wrong primary stop. What is the strongest reason?

- **A)** Twenty iterations is too low for production agents, which typically require 50 or more.
- **B)** Iteration caps cause attention dilution in the model's reasoning.
- **C)** Iteration caps should serve as a backstop against runaway loops; the loop should terminate when `stop_reason == "end_turn"`.
- **D)** The Anthropic SDK auto-manages iteration counts internally; manual caps create conflicts.

<details>
<summary>Answer</summary>

**Correct: C**

- **A wrong:** Arbitrary numbers do not address the design flaw.
- **B wrong:** Invented mechanism; attention dilution is unrelated to loop control.
- **D wrong:** The SDK does not manage iteration counts; you control the loop.

</details>

---

### Q3 (Domain 2.1)

Your agent has two tools, `lookup_order` and `get_customer`, each with a one-sentence description. The agent frequently calls the wrong one when users mention both an order ID and a customer name. What is the highest-leverage first fix?

- **A)** Add a routing layer that parses user input and pre-selects the appropriate tool before calling the model.
- **B)** Expand each tool's description to include input format, example queries, edge cases, and explicit guidance on when to use it versus the alternative.
- **C)** Merge both tools into a single `lookup_entity` tool that internally routes by identifier type.
- **D)** Add 8 to 10 few-shot examples to the system prompt showing correct tool selection.

<details>
<summary>Answer</summary>

**Correct: B**

- **A wrong:** Bypasses the LLM's natural language understanding; over-engineered as a first step.
- **C wrong:** Valid architecture but heavier than warranted for a "first step." The underlying selection problem may recur within the merged tool.
- **D wrong:** Adds token overhead on every call without fixing the root cause (the descriptions themselves).

</details>

---

### Q4 (Domain 1.6) — the trap

You are reviewing a 14-file pull request. Your plan: analyze each file individually for local issues, then run a final cross-file integration pass over all the per-file analyses. Which decomposition pattern best describes this architecture?

- **A)** Parallelization: independent per-file analyses run concurrently, results aggregated.
- **B)** Prompt chaining: sequential decomposition where each step's output feeds the next.
- **C)** Orchestrator-workers: dynamic delegation based on intermediate findings.
- **D)** Evaluator-optimizer: iterative refinement against quality criteria.

<details>
<summary>Answer</summary>

**Correct: B**

- The per-file passes look parallel, but the integration pass DEPENDS on all per-file outputs being complete first. That dependency is what makes the overall architecture chaining.
- **A wrong:** Pure parallelization aggregates independent results without a downstream step that consumes them as a dependency. The integration pass changes that.
- **C wrong:** No dynamic delegation; the structure is fixed in advance.
- **D wrong:** No evaluation-and-refine loop.

This is the trap from your prior re-quiz queue. Per-file work being parallelizable within the chain does not make the whole architecture parallelization.

</details>

---

### Q5 (Domain 2.5)

You need to find every TypeScript file in a codebase that imports from `@/lib/auth` so you can assess the blast radius of a planned refactor. Which built-in tool is the correct primary choice?

- **A)** `Glob` with pattern `**/*.ts` to enumerate all TypeScript files, then inspect each.
- **B)** `Grep` for the import string across the codebase.
- **C)** `Read` on `package.json` to identify auth-related dependencies.
- **D)** `Bash` running `npm list @/lib/auth`.

<details>
<summary>Answer</summary>

**Correct: B**

- **A wrong:** `Glob` matches file paths, not content. It cannot find import statements.
- **C wrong:** `package.json` lists dependencies, not usage sites.
- **D wrong:** `npm list` shows the dependency tree, not where code imports from a module.

</details>

---

### Q6 (Domain 5.1)

Your agent's `lookup_order` tool returns 40 fields per order, but only 4 (`order_id`, `status`, `total`, `refund_eligibility`) are relevant to the conversation flow. After 5 order lookups in a single session, the agent's context fills and response quality degrades. What is the right intervention?

- **A)** Increase `max_tokens` on each `messages.create()` call to give the model more room.
- **B)** Use a `PostToolUse` hook to trim the tool output to the 4 needed fields before it enters the conversation context.
- **C)** Spawn a subagent for each order lookup so the verbose output never reaches the main agent.
- **D)** Switch to a model with a larger context window.

<details>
<summary>Answer</summary>

**Correct: B**

- **A wrong:** `max_tokens` is the OUTPUT budget. It does not affect input context consumption.
- **C wrong:** Subagents are overkill for a deterministic field-projection. They add coordination overhead.
- **D wrong:** Papers over the root cause. Context bloat scales linearly with calls; a larger window delays the problem, it does not fix it.

</details>

---

## Scoring and advancement

| Score | Action |
|---|---|
| 6/6 | Advance to P1. |
| 5/6 | Advance to P1. Note the miss and add to spaced re-quiz queue (5-day interval). |
| 4/6 | Re-do the concept refresh on the missed concepts. Re-take a fresh quiz before advancing. |
| 3/6 or below | Phase incomplete. Do not advance. Re-build the echo agent from scratch (no copying) and re-read the relevant domain sections. |

If quiz score < 60% (3/6 or below): do not advance. The whole point of the threshold is to catch foundation gaps before they compound.

---

## Phase One Done

> **One concept that clicked.** Safety rails are what make anti-patterns observable. Without a `raise on unhandled stop_reason` check, the iteration-cap anti-pattern stays silent: the loop spins past termination, returns `None`, and produces no error. The rail is the difference between a bug you catch in minutes and one you discover in the cost dashboard.

> **One trap.** Ran break-it exercise 1 expecting the loop to spin past termination. Got a RuntimeError instead. The agent has two independent rails: an in-loop guard that crashes on any unhandled stop_reason, and a post-loop backstop that crashes a runaway. Removing the first just hands the problem to the second. A single broken edit can't make this loop fail silently, which is the point of layered rails.

> **One thing built.** `echo_agent.py`, a single-tool, single-loop reference build. `stop_reason`-driven control flow, raises on any unhandled value. Around 100 lines.



