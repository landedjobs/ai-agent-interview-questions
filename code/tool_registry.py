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
