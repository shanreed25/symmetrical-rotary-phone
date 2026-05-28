# stop_reason Control Flow and Handler Coverage

> CCA-F Phase 0 concept note. Domain 1.1 (agentic loop lifecycle).
> Core insight: a catch-all error that says "unexpected" is usually reporting *missing handler coverage*, not a genuinely anomalous value.
> [Break It Example 1a](./phase-0-plan.md#break-it-exercises-day-1-afternoon-15h)
---

## 1. The loop in one picture

An agentic loop calls the model, then branches on `stop_reason`. The reference echo agent has exactly three outcomes per iteration, plus a backstop after the loop:

```python
for iteration in range(max_iterations):
    response = client.messages.create(...)   # API call is at the TOP

    if response.stop_reason == "end_turn":   # outcome 1: terminate
        return final_text

    if response.stop_reason == "tool_use":   # outcome 2: continue
        append_assistant_turn()
        append_tool_results()
        continue

    raise RuntimeError("Unexpected stop_reason: ...")  # RAIL 1 (in-loop)

raise RuntimeError("Hit max_iterations backstop ...")  # RAIL 2 (post-loop)
```

Two things to notice, because both matter later:

- **The API call happens before any branch.** Every time the loop body runs, a call is made first, then the `stop_reason` is inspected.
- **There are two rails, not one.** Rail 1 catches a `stop_reason` the loop has no branch for. Rail 2 catches a loop that ran to its cap without ever returning. They protect against different failures.

| Rail | Where | Catches |
|---|---|---|
| Unexpected-stop_reason guard | inside the loop | a `stop_reason` value with no explicit handler |
| max_iterations backstop | after the loop | a runaway loop that exits without a return |

---

## 2. What "expected" actually means

When Rail 1 fires with `Unexpected stop_reason: 'end_turn'`, the word "unexpected" is doing something subtle.

- **To the code:** *expected* = "a value I have an explicit branch for, reached before this line." Rail 1 is the fall-through for everything not handled above it.
- **To reality:** `end_turn` is the single most normal value a model can return. It is not anomalous in any sense.

These two definitions diverge the moment you delete a handler. If you remove the `end_turn` branch, the set of values the code considers "expected" shrinks to `{tool_use}`. A perfectly ordinary value now falls through to a rail that was written for genuinely weird values (`max_tokens`, `pause_turn`, `refusal`).

**The message is honest about the code and misleading about the design.** The value is normal; the handler coverage is incomplete.

A better-worded rail would say `No handler for stop_reason 'end_turn'` rather than `Unexpected stop_reason 'end_turn'`. "Unexpected" implies the value is the problem. "No handler" points at the real cause.

---

## 3. Worked example: breaking the terminator

Both edits below replace the `end_turn` branch with an iteration cap. This is the canonical Domain 1.1 anti-pattern: using a counter as the primary stop instead of `stop_reason`.

### Edit 1a: swap the terminator, keep both rails

```python
if iteration == 5:        # was: if stop_reason == "end_turn": return ...
    break
# ... tool_use branch unchanged ...
raise RuntimeError("Unexpected stop_reason: ...")   # Rail 1 still present
```

Run input `"What is 2 plus 2?"`. The model answers directly with `end_turn` on the first call.

| iteration | API call | stop_reason | `iteration == 5`? | `tool_use`? | outcome |
|---|---|---|---|---|---|
| 0 | 1st | `end_turn` | False | False | falls to Rail 1 → **crash:** `Unexpected stop_reason: 'end_turn'` |

**Result:** crash on iteration 0, one wasted API call. Rail 1 caught the broken terminator before anything silent could happen. This is the rail doing its job.

### Edit 1b: also replace Rail 1 with `pass`

```python
if iteration == 5:
    break
# ... tool_use branch unchanged ...
pass                       # was: raise RuntimeError("Unexpected stop_reason ...")

raise RuntimeError("Hit max_iterations backstop ...")   # Rail 2 STILL present
```

Run the same input. Now `end_turn` no longer crashes; it falls through `pass` and the loop continues.

| iteration | API call | stop_reason | `iteration == 5`? | `tool_use`? | action |
|---|---|---|---|---|---|
| 0 | 1st | `end_turn` | False | False | `pass`, loop continues |
| 1 | 2nd | `end_turn` | False | False | `pass`, loop continues |
| 2 | 3rd | `end_turn` | False | False | `pass`, loop continues |
| 3 | 4th | `end_turn` | False | False | `pass`, loop continues |
| 4 | 5th | `end_turn` | False | False | `pass`, loop continues |
| 5 | 6th | `end_turn` | True | (not reached) | `break` exits loop |
| post-loop | — | — | — | — | Rail 2 → **crash:** `Hit max_iterations backstop` |

**Result:** 6 wasted API calls, then Rail 2 crashes the runaway. The model said "done" on iteration 0; the broken loop ignored that signal six times. The backstop is what stopped it from going all the way to `max_iterations`.

### The truly silent version (for contrast)

To get a loop that wastes calls and then silently returns `None` with no error, you would have to remove **both** rails and keep the `break`:

```python
if iteration == 5:
    break
# ... tool_use branch unchanged ...
pass                       # Rail 1 removed
# (Rail 2 deleted entirely)
# function falls off its end -> returns None
```

That is the worst case: no exception, no result, six wasted calls, and a `None` flowing into downstream code. It only happens when nothing is left to catch the runaway. Your reference agent never reaches this state with a single edit, which is the point of having two rails.

---

## 4. The diagnostic habit

When a catch-all error fires, do not assume the value it names is the problem. Ask one question:

> Is this `stop_reason` genuinely anomalous, or did someone delete the branch that should handle it?

- If genuinely anomalous (`refusal`, `pause_turn` you did not plan for): the rail is correctly flagging something you need to handle.
- If normal (`end_turn`, `tool_use`): the rail is reporting a hole in your control flow. The fix is upstream, not at the rail.

The same habit applies to the backstop. Rail 2 firing does not mean "raise the cap." It means "the loop is not terminating when it should; find out why." Raising the cap hides the bug and multiplies the cost.

---

## 5. Exam tie-in (Domain 1.1)

Distractors in this domain exploit the gap between *anomalous value* and *missing control flow*. Watch for:

- An answer that "fixes" a loop by **raising `max_iterations`** when the real bug is a missing or deleted `end_turn` handler. Raising the cap is treating the backstop as the primary stop, which is itself the anti-pattern.
- An answer that adds **text parsing** ("check if the response says 'done'") as the termination signal. Always wrong; `stop_reason` is the signal.
- A question that describes a normal `stop_reason` as "the error" when the snippet simply lacks a branch for it. The correct answer restores the handler, it does not treat the value as exotic.

**One-line takeaway:** terminate on `stop_reason == "end_turn"`, continue on `"tool_use"`, and treat both rails (unhandled-value guard, iteration backstop) as alarms to investigate, never as the loop's normal exit.