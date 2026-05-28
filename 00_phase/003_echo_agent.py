"""
Phase 0 - Echo Agent v0
CCA-F Foundations refresh build.

Purpose: Prove the agentic loop foundation is solid before P1 piles weight on it.

Principles this file enforces (and that you must own cold before advancing):

  1. Loop terminates on `stop_reason == "end_turn"`. Period.
  2. Iteration cap exists ONLY as a backstop against runaway loops.
  3. Tool results are appended to conversation history before the next call.
  4. NO text parsing to detect completion.
  5. NO checking for assistant text content as a completion indicator.
  6. Unexpected stop_reason values surface with context, not silent retry.

Run:
  pip install anthropic
  export ANTHROPIC_API_KEY=sk-ant-...
  python echo_agent.py "Please echo 'hello world' back to me."
"""

import os
import sys
import anthropic
import dotenv  # pip install python-dotenv

dotenv.load_dotenv()

MODEL = "claude-sonnet-4-6"

TOOLS = [
    {
        "name": "echo",
        "description": (
            "Echoes back the provided text wrapped in [ECHO: ...] markers. "
            "Call this when the user asks you to echo, repeat, or say back specific text. "
            "Input: the exact text to echo. Output: the text wrapped in [ECHO: ...]. "
            "Do not call this for general questions or arithmetic; only when the user "
            "explicitly wants text echoed."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The exact text to echo back, as the user provided it.",
                },
            },
            "required": ["text"],
        },
    }
]


def execute_tool(name: str, args: dict) -> str:
    """Server-side tool execution. Real tools hit APIs; this one just wraps."""
    if name == "echo":
        return f"[ECHO: {args['text']}]"
    raise ValueError(f"Unknown tool: {name}")


def run_agent(user_message: str, max_iterations: int = 10) -> str:# 2. Iteration cap exists ONLY as a backstop against runaway loops.
    """
    Run an agentic loop until `stop_reason == "end_turn"`.

    `max_iterations` is a BACKSTOP. The loop's job is to follow stop_reason.
    If the backstop trips, something is wrong; do not raise the cap to "fix" it.
    """
    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": user_message}]

    for iteration in range(max_iterations):
        print(f"\n--- iteration {iteration} ---", file=sys.stderr)

        response = client.messages.create(
            model=MODEL,
            max_tokens=20,
            tools=TOOLS,
            messages=messages,
        )

        print(f"stop_reason: {response.stop_reason}", file=sys.stderr)

        # PRIMARY stop condition. Nothing else terminates the loop.
        if response.stop_reason == "end_turn": # 1. Loop terminates on `stop_reason == "end_turn"`
            return "".join(b.text for b in response.content if b.type == "text")

        # Tool calls: execute, append results, continue.
        if response.stop_reason == "tool_use":
            # Append the assistant turn (preserves text + tool_use blocks together).
            messages.append({"role": "assistant", "content": response.content})

            # Execute every tool_use block in the response.
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  -> calling {block.name}({block.input})", file=sys.stderr)
                    result = execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            # Append tool_result turn (role=user by API convention).
            messages.append({"role": "user", "content": tool_results})# 3. Tool results are appended to conversation history before the next call.
            continue

        # `max_tokens`, `pause_turn`, `refusal`, etc. Do NOT silently retry.
        raise RuntimeError(
            f"Unexpected stop_reason: {response.stop_reason!r}. "
            f"This loop only handles 'end_turn' and 'tool_use'."
        )

    # Backstop tripped. Real code would log + alert.
    raise RuntimeError(
        f"Hit max_iterations backstop ({max_iterations}) without reaching end_turn. "
        "Investigate before raising the cap."
    )


def _check_env():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: set ANTHROPIC_API_KEY", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    _check_env()

    # world' back to me."1 tool call to echo, then end_turn with confirmation text. Iteration count: 2
    #==================================================================================================================
    # msg = sys.argv[1] if len(sys.argv) > 1 else "Please echo 'hello world' back to me."


    # Zero tool calls; immediate end_turn with "4" or similar. Iteration count: 1
    #==================================================================================================================
    # msg = sys.argv[1] if len(sys.argv) > 1 else "What is 2 plus 2?"


    # Either 1 response with 2 parallel tool_use blocks, OR 2 sequential iterations. Both are valid; observe which the model chose and why.
    #==================================================================================================================
    msg = sys.argv[1] if len(sys.argv) > 1 else "Echo 'first' and then echo 'second' separately."

    
    result = run_agent(msg)
    print("\n=== FINAL ===")
    print(result)
