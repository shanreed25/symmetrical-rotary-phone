# symmetrical-rotary-phone



> What you must recognize on the exam, is not the concept : the exam doesn't ask you to define concepts, it asks you to apply them in scenarios where three distractors look plausible.

> Distractors(routers, max_tokens, bigger context window) help you recognize the wrong answer. Recognizing the wrong answer is half the skill.

## [Phase 0 : Foundations Refresh](./00_phase/phase-0-plan.md)

> Purpose: Confirm your foundation is solid before P1 builds on it.

### Agentic loop lifecycle**
> **What The Exam Will Test :** That you stop on stop_reason == "end_turn" and continue on "tool_use", not by parsing text or checking for assistant content.

- `stop_reason` drives the loop: `"tool_use"` continues, `"end_turn"` terminates.


---

### Tool result handoff

> **What The Exam Will Test :** That you append BOTH the assistant turn AND a role=user turn with matched tool_result blocks before the next API call.

- After each `tool_use`, append the assistant turn AND a `role=user` turn containing `tool_result` blocks

---

### Iteration cap as backstop

> **What The Exam Will Test :** That you recognize hitting the cap as a bug to investigate, not a stop condition to design around or raise.

- Caps exist to prevent runaway costs, not to terminate normal loops. Hitting the cap signals a bug.

---

### Tool description quality

> **What The Exam Will Test :** That description quality is the first lever to pull when tools are getting misrouted, before reaching for routers, classifiers, or tool consolidation.

- Tool descriptions are the **primary** mechanism the model uses to select among tools. They should specify purpose, input format, examples, edge cases, and when to use vs alternatives. 

---

### Prompt chaining vs parallelization

> **What The Exam Will Test :** That you correctly classify a workflow as chaining when ANY downstream step depends on upstream outputs, even if some intermediate work could run in parallel. Exam version of this question always has the dependency hidden behind language that sounds parallel

- **Chaining** = sequential, each step depends on the prior. **Parallelization** = independent work, results aggregated. A per-file pass + an integration pass is chaining (the integration step depends on the per-file outputs).

---

### Built-in tool selection (Grep / Glob / Read / Edit)

> **What The Exam Will Test :** That you pick the right tool by purpose (Grep for content, Glob for paths, Read for full file, Edit for unique-anchor edits) and know Read + Write is the fallback when Edit's anchor isn't unique.

- `Grep` = content search. `Glob` = filename/path patterns. `Read` = full file. `Edit` = targeted edit by unique anchor; fall back to `Read`+`Write` when anchor isn't unique.

---

### Verbose tool output trimming

> **What The Exam Will Test :** That you trim at the source (wrapper or PostToolUse hook) and reject distractors like raising max_tokens, switching to a bigger context window, or summarizing history.

- Tools that return 40+ fields when 4 are needed will saturate context across a session. Trim at the source (the tool wrapper) or via a `PostToolUse` hook before the result enters context.

---
