"""A minimal agent loop with the guards interviewers ask about.

Provider-agnostic: `model` is any callable that takes (messages, tool_schemas)
and returns a ModelTurn. Swap in an Anthropic or OpenAI adapter in a few lines.
Runs with the scripted fake model at the bottom, no API key needed.
"""

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Callable, Literal

from tool_registry import ToolRegistry


@dataclass
class ToolCall:
    id: str
    name: str
    args: dict


@dataclass
class ModelTurn:
    text: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class RunResult:
    status: Literal["done", "max_steps", "budget", "stuck", "denied"]
    answer: str | None
    steps: int
    tokens: int
    transcript: list[dict]


Model = Callable[[list[dict], list[dict]], ModelTurn]
Approver = Callable[[ToolCall], bool]


def run_agent(
    model: Model,
    registry: ToolRegistry,
    task: str,
    system: str = "You are a careful agent. Use tools when you need facts. Stop when the task is done.",
    max_steps: int = 10,
    max_tokens: int = 50_000,
    approve: Approver = lambda call: False,
    max_result_chars: int = 4_000,
) -> RunResult:
    messages: list[dict] = [{"role": "system", "content": system}, {"role": "user", "content": task}]
    schemas = registry.schemas()
    tokens = 0
    seen_calls: dict[str, int] = {}

    for step in range(1, max_steps + 1):
        turn = model(messages, schemas)
        tokens += turn.input_tokens + turn.output_tokens
        messages.append({
            "role": "assistant",
            "content": turn.text,
            "tool_calls": [c.__dict__ for c in turn.tool_calls],
        })

        if not turn.tool_calls:
            return RunResult("done", turn.text, step, tokens, messages)
        if tokens > max_tokens:
            return RunResult("budget", None, step, tokens, messages)

        for call in turn.tool_calls:
            fingerprint = f"{call.name}:{json.dumps(call.args, sort_keys=True)}"
            seen_calls[fingerprint] = seen_calls.get(fingerprint, 0) + 1
            if seen_calls[fingerprint] > 2:
                return RunResult("stuck", None, step, tokens, messages)

        def execute(call: ToolCall) -> dict:
            tool = registry.find(call.name)
            if tool is not None and tool.destructive and not approve(call):
                return {"error": {"kind": "denied", "message": "a human declined this action", "retryable": False}}
            return registry.call(call.name, call.args)

        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(execute, turn.tool_calls))

        for call, result in zip(turn.tool_calls, results):
            body = json.dumps(result)
            if len(body) > max_result_chars:
                body = body[:max_result_chars] + f'... [truncated {len(body) - max_result_chars} chars; narrow the query]'
            messages.append({"role": "tool", "tool_call_id": call.id, "content": body})

    return RunResult("max_steps", None, max_steps, tokens, messages)


class ScriptedModel:
    """Plays back fixed turns. Lets you unit-test the loop without a real model."""

    def __init__(self, turns: list[ModelTurn]):
        self.turns = list(turns)
        self.seen: list[list[dict]] = []

    def __call__(self, messages: list[dict], tools: list[dict]) -> ModelTurn:
        self.seen.append(list(messages))
        return self.turns.pop(0)


if __name__ == "__main__":
    registry = ToolRegistry()

    @registry.register(order_id="Order id like 'A-1042'.")
    def get_order(order_id: str) -> dict:
        """Look up one order by id. Returns status and amount."""
        return {"order_id": order_id, "status": "delivered", "amount": 42.0}

    @registry.register(destructive=True)
    def refund_order(order_id: str, amount: float) -> str:
        """Refund an order. Irreversible. Needs human approval."""
        return f"refunded {amount} on {order_id}"

    model = ScriptedModel([
        ModelTurn(tool_calls=[ToolCall("t1", "get_order", {"order_id": "A-1042"})], input_tokens=900, output_tokens=40),
        ModelTurn(tool_calls=[ToolCall("t2", "refund_order", {"order_id": "A-1042", "amount": 42.0})], input_tokens=1100, output_tokens=40),
        ModelTurn(text="The refund needs approval, so I opened a ticket instead.", input_tokens=1300, output_tokens=30),
    ])
    result = run_agent(model, registry, "Refund order A-1042", approve=lambda call: False)
    print(result.status, result.steps, result.tokens)
    print(result.answer)
    for m in result.transcript:
        if m["role"] == "tool":
            print("tool ->", m["content"])
