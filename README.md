# symmetrical-rotary-phone


## [Phase 00](./00_phase/phase-0-plan.md)

- **Agentic loop lifecycle**
    - `stop_reason` drives the loop: `"tool_use"` continues, `"end_turn"` terminates.
- **Tool result handoff**
    - After each `tool_use`, append the assistant turn AND a `role=user` turn containing `tool_result` blocks
- **Iteration cap as backstop**
    - Caps exist to prevent runaway costs, not to terminate normal loops. Hitting the cap signals a bug.
- **Tool description quality**
    - Tool descriptions are the **primary** mechanism the model uses to select among tools. They should specify purpose, input format, examples, edge cases, and when to use vs alternatives. 
- **Prompt chaining vs parallelization**
    - **Chaining** = sequential, each step depends on the prior. **Parallelization** = independent work, results aggregated. A per-file pass + an integration pass is chaining (the integration step depends on the per-file outputs).
- **Built-in tool selection (Grep / Glob / Read / Edit)**
    - `Grep` = content search. `Glob` = filename/path patterns. `Read` = full file. `Edit` = targeted edit by unique anchor; fall back to `Read`+`Write` when anchor isn't unique.
- **Verbose tool output trimming**
    - Tools that return 40+ fields when 4 are needed will saturate context across a session. Trim at the source (the tool wrapper) or via a `PostToolUse` hook before the result enters context.