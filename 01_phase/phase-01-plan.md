# CCA-F Phase 1 — Single-Agent Loop Mastery

> **Purpose:** Take the P0 loop and make it do real work: multiple tools, multi-turn tool cycling, and the chain-vs-parallel distinction live in your own code.
> **Build flavor:** Generic (weather + calculator). Spine project (customer support) starts in P2.
> **Duration target:** 5 to 7 days.
> **Advancement gate:** build passes all 5 acceptance tests + P1 quiz at 85% (quiz drafted after you build).

> Quiz and Mochi deck are intentionally NOT in this file. They'll be written after you build, so they can target the mistakes you actually make.

---

## What's new in P1 (vs P0)

P0 proved you can run a loop that terminates correctly. P1 is about what happens *inside* a loop that runs several times for a single user request. The loop control flow does not change. What changes is tool selection, sequencing, and state.

| P0 had | P1 adds |
|---|---|
| 1 tool | 2 tools the model must choose between |
| At most 1 tool call | Several tool calls across multiple iterations |
| Trivial echo | Real tool output that the model reasons about |
| Loop control as the lesson | Tool selection + sequencing as the lesson |

---

## Concept refresh (6 concepts)

| # | Concept | Core fact | Anti-pattern |
|---|---|---|---|
| 1 | **Multi-turn state accumulation** | For one user request, the loop may run several times. Each iteration appends the assistant turn and a tool_result turn, so history grows. The model reasons over the *accumulated* history each call. | Sending only the latest turn instead of the full history; the model loses what it already learned. |
| 2 | **Tool selection** | With 2+ tools, the model picks which to call based on the user's request and each tool's description. Selection is the model's job, not a router's. | Building a keyword router that pre-selects the tool and bypasses the model's understanding. |
| 3 | **Tool description as a *when* signal** | A description does two jobs: says what the tool does AND when to call it vs alternatives. The "when" is what drives correct selection. | One-word descriptions ("Weather", "Math") that say what but not when. Tolerable for very distinct tools, dangerous for similar ones (the P2 lesson). |
| 4 | **Tool chaining inside a loop** | When tool B needs tool A's output, the model calls A, sees the result in the next iteration's history, then calls B. The dependency forces sequential iterations. | Calling this "parallel." If B needs A's output, it is a chain, full stop. |
| 5 | **Parallel tool calls** | When two tools are independent, the model can emit multiple `tool_use` blocks in a SINGLE response. You execute all of them and return all results in one tool_result turn. | Forcing independent calls into separate iterations and calling it "necessary sequencing." |
| 6 | **`tool_choice` options** | `auto` (model decides whether to call a tool), `any` (must call some tool, model picks which), forced `{"type":"tool","name":"X"}` (must call tool X). | Forcing a tool when the right answer is no tool at all (e.g. forcing `get_weather` on "hello"). |

### The one to watch: 4 vs 5

This is your re-quiz weak spot at full size. The single discriminator:

> **Does the second tool need the first tool's output?**
> Yes → chain (sequential iterations, dependency).
> No → parallel (can be one response, multiple `tool_use` blocks).

Your build has one test for each. Run them back to back and watch the iteration traces differ.

---

## Build spec: v1 two-tool agent

You write this. Reuse your P0 loop **verbatim**, including both rails. Do not rewrite the loop; the point is to confirm the same control flow handles multiple tools and multiple iterations without changes.

### Tools to implement

**Tool 1: `get_weather`**
- Inputs: `location` (string, required), `unit` (enum `celsius`/`fahrenheit`, optional).
- Behavior: mock. Return a plausible fixed temperature for the location and unit. No real API. Example: `{"location": "Las Vegas, NV", "temp": 95, "unit": "fahrenheit"}`.
- You write the description. Make it specify when to call it.

**Tool 2: `calculate`**
- Inputs: `expression` (string, required), e.g. `"95 * 2"`.
- Behavior: evaluate a simple arithmetic expression and return the number.
- You write the description.

> **Teaching-lens flag (do not skip).** The obvious way to implement `calculate` is `eval(expression)`. Do not. `eval()` on model-supplied (and ultimately user-influenced) input is a remote-code-execution footgun: a crafted expression can run arbitrary Python. Use a constrained evaluator instead, e.g. parse with `ast.parse(expr, mode="eval")` and walk the tree allowing only numeric literals and arithmetic operators, or use a small allowlist. The exam won't test `eval` safety directly, but you are building habits for production agents where tool inputs are attacker-reachable.

### What you must NOT do

- Do not write a router that inspects the user message and picks the tool. The model selects via descriptions. That is the whole exercise.
- Do not parse text for completion. `stop_reason` only.
- Do not change the loop's stop logic from P0.

---

## Acceptance tests

Run each, inspect the stderr iteration trace, confirm behavior.

| # | Input | Expected behavior | What it proves |
|---|---|---|---|
| 1 | `"What's the weather in Las Vegas?"` | 1 call to `get_weather`, then `end_turn`. | Single-tool selection. |
| 2 | `"What's 47 times 13?"` | 1 call to `calculate`, then `end_turn`. | Selecting the *other* tool correctly. |
| 3 | `"Hi, how are you?"` | Zero tool calls, immediate `end_turn`. | Model declines to force a tool when none fits (concept 6). |
| 4 (chain) | `"What's the temperature in Las Vegas in fahrenheit, and what is that number doubled?"` | `get_weather` first, then in a later iteration `calculate` using the returned temp. Sequential iterations. | **Concept 4.** The doubling DEPENDS on the weather result. Watch history carry the temp forward. |
| 5 (parallel) | `"What's the weather in Las Vegas and separately what's 8 times 9?"` | The two needs are independent. Model may emit both `tool_use` blocks in ONE response; you execute both and return both results in one tool_result turn. | **Concept 5.** Independent work, no dependency. |

> Tests 4 and 5 are the heart of P1. If 4 runs in parallel or 5 runs as a forced chain, dig into why before advancing. The model's choice should track the dependency.

---

## Break-it exercises

Introduce each, run the relevant test, observe, then revert. One log sentence each.

1. **Starve the descriptions.** Replace both tool descriptions with one word each (`"Weather"`, `"Math"`). Run tests 1, 2, 4. Likely finding: selection still mostly works, because weather and arithmetic are very distinct domains. **That finding IS the lesson:** distinct tools tolerate weak descriptions; similar tools do not. P2 will give you 4 similar tools where this breaks hard.
2. **Force the wrong tool.** Set `tool_choice={"type":"tool","name":"get_weather"}` and run test 2 (the calculator query). Observe the model calling `get_weather` on a math question because you removed its choice. Lesson: forced `tool_choice` overrides selection entirely; use it deliberately.
3. **Break the chain dependency.** In test 4, modify `get_weather` to return the temp as a word (`"ninety-five"`) instead of a number. Run it. Observe whether `calculate` gets a malformed expression and how the loop handles it. Lesson: tool output format is part of the contract between chained tools.

---

## Advancement gate

| Condition | Action |
|---|---|
| All 5 acceptance tests pass + quiz ≥ 85% | Advance to P2 (MCP tools, spine project begins). |
| Tests pass, quiz 60 to 84% | Re-quiz the weak subdomain at 5-day interval, then advance. |
| Any acceptance test fails and you can't explain why | Phase incomplete. Debug to root cause first. |
| Test 4 runs parallel or test 5 runs as a chain, unexplained | Stop. This is the weak spot resurfacing. Resolve before advancing. |

When the build passes all 5 tests, tell me which behaviors you saw on tests 4 and 5 (sequential vs parallel, iteration counts), and I'll draft the quiz + Mochi deck targeted to what actually happened.

---

## Friday log template

```
Phase 1 done.

One concept that clicked:
  [chain vs parallel, in your own words]

One trap I fell into:
  [a tool-selection or sequencing surprise]

One thing I built:
  v1 two-tool agent — weather + calculator, P0 loop reused unchanged,
  safe arithmetic eval (no raw eval()).

What's next: Phase 2, MCP tools and the start of the support-agent spine.
```