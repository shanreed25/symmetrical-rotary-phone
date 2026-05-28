# CCA-F :: P0 :: Foundations

> Mochi import: New Deck → Import → Markdown file. Each `##` heading starts a card. The `---` horizontal rule separates front from back.

## Agentic loop: primary stop signal

What's the primary termination signal for the agentic loop?

---

`stop_reason == "end_turn"`. Continue when `stop_reason == "tool_use"`. Iteration caps are backstops, not primary stops. Text content presence is NOT a stop signal.

Tags: `cca-f` `p0` `domain-1-1`

## Agentic loop: iteration cap purpose

What is the role of `max_iterations` in an agentic loop?

---

Backstop against runaway loops. Tripping it signals a bug. NEVER design the loop's normal exit around the cap. NEVER raise the cap to "fix" tripping; investigate first.

Tags: `cca-f` `p0` `domain-1-1`

## Agentic loop: tool result handoff order

After `stop_reason == "tool_use"`, in what order do you append messages before the next API call?

---

1. Append the assistant turn (the entire `response.content`, which contains text + tool_use blocks).
2. Append a `role=user` turn whose content is a list of `tool_result` blocks (one per tool_use, matched by `tool_use_id`).

Both turns must be in history before the next `messages.create()`.

Tags: `cca-f` `p0` `domain-1-1`

## Agentic loop: anti-patterns

Name three anti-patterns for detecting loop termination.

---

1. Parsing natural language for "done" / "final answer" / "in conclusion".
2. Using iteration cap as the primary stop (instead of as a backstop).
3. Checking for assistant text content presence as a completion indicator (tool_use responses can include reasoning text).

Tags: `cca-f` `p0` `domain-1-1`

## Tool descriptions: primary selection mechanism

What is the primary mechanism LLMs use to select among available tools?

---

The tool **description**. Minimal or overlapping descriptions cause misrouting. Good descriptions specify: purpose, input format, example queries, edge cases, when to use vs alternatives.

Tags: `cca-f` `p0` `domain-2-1`

## Tool descriptions: first fix for misrouting

Two tools with one-line descriptions are getting misrouted. What's the highest-leverage first fix?

---

Expand each description to clearly differentiate purpose, inputs, outputs, and when to use vs the other. Splitting/merging tools or adding routing layers are heavier moves and not the first step.

Tags: `cca-f` `p0` `domain-2-1`

## Prompt chaining: definition

What is prompt chaining?

---

A sequential decomposition where each step's output feeds the next step's input. The downstream step DEPENDS on upstream completion. Used for predictable multi-aspect work.

Tags: `cca-f` `p0` `domain-1-6`

## Parallelization: definition

What is the parallelization pattern (in agent decomposition)?

---

Independent subtasks run concurrently; their results are aggregated. NO subtask depends on another's output. If a downstream step needs all results first, the overall pattern is chaining, not parallelization.

Tags: `cca-f` `p0` `domain-1-6`

## The chaining-vs-parallel trap

Per-file analysis on 14 files + a final cross-file integration pass. What pattern?

---

**Prompt chaining.** The per-file analyses look parallel, BUT the integration pass depends on all per-file outputs being complete. That dependency makes the overall architecture chaining. Per-file work being parallelizable WITHIN the chain doesn't change the top-level pattern.

Tags: `cca-f` `p0` `domain-1-6` `trap`

## Built-in tool: Grep

When do you use `Grep`?

---

To search file CONTENT for patterns (function names, error messages, import statements, regex matches). Returns matching lines from across files. Does NOT match filenames.

Tags: `cca-f` `p0` `domain-2-5`

## Built-in tool: Glob

When do you use `Glob`?

---

To find files by PATH or NAME pattern (e.g. `**/*.test.tsx`). Returns paths only, NOT contents. Use to enumerate files for a follow-up `Read` or `Grep`.

Tags: `cca-f` `p0` `domain-2-5`

## Built-in tool: Edit vs Read+Write

When does `Edit` fail, and what's the fallback?

---

`Edit` requires its anchor text to be unique in the file. If the anchor appears more than once, `Edit` fails. Fallback: `Read` the full file, modify in memory, `Write` it back.

Tags: `cca-f` `p0` `domain-2-5`

## Context bloat: root cause

Why does context degrade after 5 verbose tool calls in one session?

---

Tool outputs accumulate in the conversation history and consume input context tokens disproportionately to their relevance (e.g. 40 fields returned when 4 are needed). After several calls, important earlier signal gets diluted or pushed past the model's attention.

Tags: `cca-f` `p0` `domain-5-1`

## Context bloat: the fix

Tool returns 40 fields, you need 4. How do you prevent context bloat?

---

Trim at the source: either project the response in the tool wrapper itself, OR use a `PostToolUse` hook to normalize/reduce before the result enters context. NOT `max_tokens` (output budget), NOT a bigger context window (papers over the problem).

Tags: `cca-f` `p0` `domain-5-1`

## stop_reason values: handling unexpected ones

Your loop sees `stop_reason == "max_tokens"`. What do you do?

---

Surface it. Do NOT silently retry. Raise with context that includes the stop_reason value. Common unexpected values: `"max_tokens"`, `"pause_turn"`, `"refusal"`. The loop should only treat `"end_turn"` and `"tool_use"` as known; everything else is a bug to investigate.

Tags: `cca-f` `p0` `domain-1-1`
