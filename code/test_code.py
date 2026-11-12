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
