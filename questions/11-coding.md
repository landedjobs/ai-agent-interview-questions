# Coding exercises

<sub>[Question index](README.md) · [Repo home](../README.md) · Previous: [System design scenarios](10-system-design.md)</sub>

4 exercises, Q111 to Q114. Agent coding rounds rarely ask for algorithms. They ask you to build the loop, a tool layer, or a reliability wrapper in 30 to 45 minutes, then extend it when the interviewer adds a twist. The code here is original, uses the Python standard library only, and runs without an API key. It lives in [`code/`](../code/), with tests:

```bash
cd code
python3 -m unittest test_code -v
python3 agent_loop.py
```

Difficulty is `Core` or `Senior`. All four are `Representative`.

---

<a id="q111"></a>
### Q111. Build a minimal agent loop in Python.

`Core` · `Representative`

**What the interviewer wants.** A loop that calls the model with tools, runs tool calls, feeds results back with their call ids, and stops on a final answer. Then the guards: max steps, a token budget, repeated-call detection, approval for destructive tools, truncation of big results. Keep the model behind an interface so you can test with a fake.

**Talk track.** Say the stop conditions before you write the loop. Say that errors go back to the model as data. Say why the history is re-sent each turn (the model is stateless) and what that does to cost.

```python
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
```

**Follow-ups**
- *Add streaming.* Yield text deltas to the caller while accumulating tool call arguments; run tools only when the turn completes.
- *Make it resumable.* Persist `messages`, step and token counts after each step, keyed by run id; on restart, load and continue.
- *Swap in a real provider.* Write an adapter that maps `messages` and `tool_schemas` to the provider's format and maps its response into `ModelTurn`. Nothing else changes.

---

<a id="q112"></a>
### Q112. Build a tool registry that generates schemas and validates calls.

`Core` · `Representative`

**What the interviewer wants.** A decorator that turns a typed Python function into a tool with a JSON Schema, a lookup by name, and validation that returns errors the model can act on, instead of raising into the loop.

**Talk track.** Point out the choices: `additionalProperties: false` so invented arguments fail loudly, `Literal` types become enums, defaults are not required, unknown tool names return the list of real ones, and a crash inside a tool becomes a `tool_crashed` result rather than killing the run.

```python
"""A small tool registry: register Python functions, export JSON schemas, validate calls.

Standard library only. The schema builder covers the types agents use most
(str, int, float, bool, list, Literal enums, Optional) and nothing more.
"""

import inspect
import json
import typing
from dataclasses import dataclass, field
from typing import Any, Callable, Literal, get_args, get_origin

_PRIMITIVES = {str: "string", int: "integer", float: "number", bool: "boolean"}


class ToolError(Exception):
    """An error the model should see and can act on."""

    def __init__(self, kind: str, message: str, retryable: bool = False):
        super().__init__(message)
        self.kind = kind
        self.retryable = retryable

    def to_result(self) -> dict:
        return {"error": {"kind": self.kind, "message": str(self), "retryable": self.retryable}}


def _schema_for(tp: Any) -> dict:
    origin = get_origin(tp)
    if tp in _PRIMITIVES:
        return {"type": _PRIMITIVES[tp]}
    if origin is Literal:
        values = list(get_args(tp))
        return {"type": _PRIMITIVES[type(values[0])], "enum": values}
    if origin in (list, typing.List):
        (item,) = get_args(tp) or (str,)
        return {"type": "array", "items": _schema_for(item)}
    if origin is typing.Union:
        non_null = [a for a in get_args(tp) if a is not type(None)]
        if len(non_null) == 1:
            return _schema_for(non_null[0])
    raise TypeError(f"unsupported parameter type: {tp!r}")


@dataclass
class Tool:
    name: str
    description: str
    fn: Callable[..., Any]
    parameters: dict
    destructive: bool = False
    hints: dict = field(default_factory=dict)

    def schema(self) -> dict:
        return {"name": self.name, "description": self.description, "input_schema": self.parameters}


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, name: str | None = None, destructive: bool = False, **param_docs: str):
        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            tool_name = name or fn.__name__
            if tool_name in self._tools:
                raise ValueError(f"duplicate tool name: {tool_name}")
            hints = typing.get_type_hints(fn)
            props, required = {}, []
            for pname, param in inspect.signature(fn).parameters.items():
                prop = _schema_for(hints[pname])
                if pname in param_docs:
                    prop["description"] = param_docs[pname]
                if param.default is inspect.Parameter.empty:
                    required.append(pname)
                else:
                    prop["default"] = param.default
                props[pname] = prop
            parameters = {
                "type": "object",
                "properties": props,
                "required": required,
                "additionalProperties": False,
            }
            description = inspect.getdoc(fn) or ""
            self._tools[tool_name] = Tool(tool_name, description, fn, parameters, destructive, hints)
            return fn

        return decorator

    def schemas(self, names: list[str] | None = None) -> list[dict]:
        chosen = names if names is not None else sorted(self._tools)
        return [self._tools[n].schema() for n in chosen]

    def find(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            known = ", ".join(sorted(self._tools))
            raise ToolError("unknown_tool", f"no tool named {name!r}. Available tools: {known}")
        return self._tools[name]

    def validate(self, tool: Tool, args: dict) -> dict:
        props = tool.parameters["properties"]
        extra = set(args) - set(props)
        if extra:
            raise ToolError("invalid_arguments", f"unexpected arguments {sorted(extra)}; allowed: {sorted(props)}")
        missing = [p for p in tool.parameters["required"] if p not in args]
        if missing:
            raise ToolError("invalid_arguments", f"missing required arguments {missing}")
        for pname, value in args.items():
            spec = props[pname]
            if "enum" in spec and value not in spec["enum"]:
                raise ToolError("invalid_arguments", f"{pname} must be one of {spec['enum']}, got {value!r}")
            expected = spec["type"]
            ok = {
                "string": isinstance(value, str),
                "integer": isinstance(value, int) and not isinstance(value, bool),
                "number": isinstance(value, (int, float)) and not isinstance(value, bool),
                "boolean": isinstance(value, bool),
                "array": isinstance(value, list),
            }[expected]
            if not ok:
                raise ToolError("invalid_arguments", f"{pname} must be {expected}, got {type(value).__name__}")
        return args

    def call(self, name: str, args: dict) -> dict:
        try:
            tool = self.get(name)
            self.validate(tool, args)
            return {"ok": tool.fn(**args)}
        except ToolError as err:
            return err.to_result()
        except Exception as err:
            return ToolError("tool_crashed", f"{type(err).__name__}: {err}").to_result()


if __name__ == "__main__":
    registry = ToolRegistry()

    @registry.register(units="Temperature units for the reply.")
    def get_weather(city: str, units: Literal["c", "f"] = "c") -> str:
        """Current weather for one city. Use the city name as a user would write it, e.g. "Berlin"."""
        return f"18 degrees {units} and cloudy in {city}"

    print(json.dumps(registry.schemas(), indent=4))
    print(registry.call("get_weather", {"city": "Berlin"}))
    print(registry.call("get_weather", {"city": "Berlin", "units": "kelvin"}))
    print(registry.call("get_wether", {"city": "Berlin"}))
```

**Follow-ups**
- *Support nested objects.* Accept dataclasses or TypedDicts and recurse; or use Pydantic and export its JSON Schema.
- *Add per-tool timeouts.* Run each call in a worker with a deadline and return a `timeout` error marked retryable.
- *Add permissions.* Store required scopes on each tool and check them against the run's grants in `call`.

---

<a id="q113"></a>
### Q113. Write a retry wrapper for tool and model calls.

`Senior` · `Representative`

**What the interviewer wants.** Exponential backoff with jitter, a cap on attempts, a total deadline, honouring `retry_after`, retrying only transient errors, and one idempotency key reused across attempts so retried writes do not double-apply.

**Talk track.** Explain full jitter (random wait between zero and the capped backoff) and why it avoids synchronised retry waves. Explain why the key is generated once outside the loop. Mention that stacking retries at several layers multiplies calls.

```python
"""Retry wrapper for agent tool calls and model calls.

Exponential backoff with full jitter, a total deadline, a retryable check,
and one idempotency key per logical operation so a retried write does not
run twice on a server that honours the key.
"""

import random
import time
import uuid
from dataclasses import dataclass
from typing import Callable, TypeVar

T = TypeVar("T")


class TransientError(Exception):
    """Timeouts, 429s, 5xx. Safe to retry if the operation is idempotent."""

    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class PermanentError(Exception):
    """Bad input, auth failure, policy refusal. Retrying will not help."""


@dataclass
class RetryPolicy:
    max_attempts: int = 4
    base_delay: float = 0.5
    max_delay: float = 8.0
    deadline: float = 30.0

    def delay(self, attempt: int, retry_after: float | None) -> float:
        if retry_after is not None:
            return min(retry_after, self.max_delay)
        cap = min(self.max_delay, self.base_delay * (2 ** attempt))
        return random.uniform(0, cap)


def call_with_retry(
    op: Callable[[str], T],
    policy: RetryPolicy = RetryPolicy(),
    is_retryable: Callable[[Exception], bool] = lambda e: isinstance(e, TransientError),
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
    idempotency_key: str | None = None,
) -> T:
    """Run op(idempotency_key) until it succeeds, fails permanently, or runs out of budget.

    The same key goes to every attempt. That is the whole point: the server
    uses it to return the first result instead of performing the write again.
    """
    key = idempotency_key or str(uuid.uuid4())
    started = clock()
    last_error: Exception | None = None
    for attempt in range(policy.max_attempts):
        try:
            return op(key)
        except Exception as err:
            last_error = err
            if not is_retryable(err):
                raise
            if attempt == policy.max_attempts - 1:
                break
            wait = policy.delay(attempt, getattr(err, "retry_after", None))
            if clock() - started + wait > policy.deadline:
                break
            sleep(wait)
    raise TimeoutError(f"gave up after {attempt + 1} attempts: {last_error}") from last_error


if __name__ == "__main__":
    calls = {"n": 0}
    seen_keys = set()

    def flaky_charge(key: str) -> str:
        calls["n"] += 1
        seen_keys.add(key)
        if calls["n"] < 3:
            raise TransientError("upstream 503")
        return f"charged once under key {key[:8]}"

    print(call_with_retry(flaky_charge, sleep=lambda s: None))
    print(f"attempts={calls['n']} distinct_keys={len(seen_keys)}")
```

**Follow-ups**
- *Add a circuit breaker.* Count failures per dependency in a window; when open, fail fast for a cooldown, then let one probe through.
- *Async version.* Same logic with `asyncio.sleep` and `async def op`.
- *How would you test timing without sleeping?* Inject `sleep` and `clock`, as the function does, and assert on the recorded waits.

---

<a id="q114"></a>
### Q114. Test an agent loop without calling a model.

`Senior` · `Representative`

**What the interviewer wants.** Proof that you test the harness deterministically. A scripted fake model plays back fixed turns, so you can assert that the loop runs tools, passes results back, stops on limits, denies unapproved destructive calls and retries correctly. Model quality is the eval suite's job; harness correctness is a unit test's job.

```python
import unittest
from typing import Literal

from agent_loop import ModelTurn, ScriptedModel, ToolCall, run_agent
from retry import PermanentError, RetryPolicy, TransientError, call_with_retry
from tool_registry import ToolRegistry


def make_registry() -> ToolRegistry:
    registry = ToolRegistry()

    @registry.register()
    def add(a: int, b: int) -> int:
        """Add two integers."""
        return a + b

    @registry.register()
    def mode(kind: Literal["fast", "slow"] = "fast") -> str:
        """Pick a mode."""
        return kind

    @registry.register(destructive=True)
    def delete_file(path: str) -> str:
        """Delete a file. Irreversible."""
        return f"deleted {path}"

    return registry


class RegistryTests(unittest.TestCase):
    def test_schema_has_required_and_enum(self):
        schemas = {s["name"]: s for s in make_registry().schemas()}
        self.assertEqual(schemas["add"]["input_schema"]["required"], ["a", "b"])
        self.assertEqual(schemas["mode"]["input_schema"]["properties"]["kind"]["enum"], ["fast", "slow"])

    def test_bad_arguments_come_back_as_data(self):
        registry = make_registry()
        self.assertEqual(registry.call("add", {"a": 1, "b": 2}), {"ok": 3})
        self.assertEqual(registry.call("add", {"a": "1", "b": 2})["error"]["kind"], "invalid_arguments")
        self.assertEqual(registry.call("mode", {"kind": "medium"})["error"]["kind"], "invalid_arguments")
        self.assertEqual(registry.call("nope", {})["error"]["kind"], "unknown_tool")


class LoopTests(unittest.TestCase):
    def test_tool_then_answer(self):
        model = ScriptedModel([
            ModelTurn(tool_calls=[ToolCall("1", "add", {"a": 2, "b": 3})]),
            ModelTurn(text="5"),
        ])
        result = run_agent(model, make_registry(), "2+3?")
        self.assertEqual((result.status, result.answer, result.steps), ("done", "5", 2))
        self.assertIn('"ok": 5', model.seen[1][-1]["content"])

    def test_destructive_tool_needs_approval(self):
        model = ScriptedModel([
            ModelTurn(tool_calls=[ToolCall("1", "delete_file", {"path": "/tmp/x"})]),
            ModelTurn(text="not deleted"),
        ])
        result = run_agent(model, make_registry(), "delete it", approve=lambda c: False)
        self.assertIn("denied", result.transcript[-2]["content"])

    def test_repeated_identical_call_stops(self):
        turns = [ModelTurn(tool_calls=[ToolCall(str(i), "add", {"a": 1, "b": 1})]) for i in range(5)]
        result = run_agent(ScriptedModel(turns), make_registry(), "loop")
        self.assertEqual(result.status, "stuck")

    def test_max_steps(self):
        turns = [ModelTurn(tool_calls=[ToolCall(str(i), "add", {"a": i, "b": 1})]) for i in range(5)]
        result = run_agent(ScriptedModel(turns), make_registry(), "go", max_steps=3)
        self.assertEqual(result.status, "max_steps")


class RetryTests(unittest.TestCase):
    def test_same_key_every_attempt(self):
        keys = []

        def op(key):
            keys.append(key)
            if len(keys) < 3:
                raise TransientError("503")
            return "ok"

        self.assertEqual(call_with_retry(op, sleep=lambda s: None), "ok")
        self.assertEqual(len(set(keys)), 1)

    def test_permanent_error_is_not_retried(self):
        calls = []

        def op(key):
            calls.append(key)
            raise PermanentError("400")

        with self.assertRaises(PermanentError):
            call_with_retry(op, sleep=lambda s: None)
        self.assertEqual(len(calls), 1)

    def test_gives_up(self):
        def op(key):
            raise TransientError("503")

        with self.assertRaises(TimeoutError):
            call_with_retry(op, policy=RetryPolicy(max_attempts=3), sleep=lambda s: None)


if __name__ == "__main__":
    unittest.main()
```

**Follow-ups**
- *What would you add next?* A test that a truncated tool result includes the "narrow the query" hint, and one that parallel calls keep result order.
- *How do you test prompts?* Not here. Prompts go through the eval suite with real model calls and graders.

---

<sub>[Question index](README.md) · [Repo home](../README.md)</sub>
