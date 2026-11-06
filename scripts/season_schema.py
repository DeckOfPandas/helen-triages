"""A JSON Schema validator for the keywords Rhubarb's season schema uses.

It handles exactly those keywords and refuses a schema naming any other, so a
schema that grows a keyword cannot be half-checked here: support it first.
Rhubarb checks the same file with its own twin, tools/schema-check.js, which
refuses the same way. No dependency: the test requirements stay pinned as
they are.

    from season_schema import validate
    validate(schema, data)   # a list of problems, empty when valid
"""
from __future__ import annotations

import json
import re

ANNOTATIONS = {"$schema", "$id", "title", "description"}
KEYWORDS = {"type", "required", "properties", "additionalProperties", "items",
            "const", "enum", "minItems", "maxItems", "minLength", "pattern"}
TYPES = {"object": dict, "array": list, "string": str, "boolean": bool}


def _check_schema(schema: dict, where: str) -> list[str]:
    problems = [f'{where}: schema keyword "{k}" is not supported by scripts/season_schema.py'
                for k in schema if k not in ANNOTATIONS and k not in KEYWORDS]
    if "additionalProperties" in schema and schema["additionalProperties"] is not False:
        problems.append(f'{where}: only "additionalProperties": false is supported')
    if "type" in schema and schema["type"] not in TYPES:
        problems.append(f'{where}: type "{schema["type"]}" is not supported')
    for name, sub in (schema.get("properties") or {}).items():
        problems += _check_schema(sub, f"{where}.properties.{name}")
    if "items" in schema:
        problems += _check_schema(schema["items"], f"{where}.items")
    return problems


def _same(a, b) -> bool:
    # JSON equality: in Python True == 1, which JSON does not allow.
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def _type_ok(value, name: str) -> bool:
    if name == "boolean":
        return isinstance(value, bool)
    return isinstance(value, TYPES[name]) and not isinstance(value, bool)


def _check(schema: dict, data, at: str, out: list[str]) -> None:
    if "const" in schema and not _same(schema["const"], data):
        out.append(f"{at}: must be {json.dumps(schema['const'])}")
    if "enum" in schema and not any(_same(e, data) for e in schema["enum"]):
        out.append(f"{at}: {json.dumps(data)} is not one of {', '.join(map(str, schema['enum']))}")
    if "type" in schema and not _type_ok(data, schema["type"]):
        out.append(f"{at}: must be {schema['type']}, is {type(data).__name__}")
        return
    if isinstance(data, str):
        if len(data) < schema.get("minLength", 0):
            out.append(f"{at}: shorter than {schema['minLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], data):
            out.append(f"{at}: {json.dumps(data)} does not match {schema['pattern']}")
    if isinstance(data, list):
        if len(data) < schema.get("minItems", 0):
            out.append(f"{at}: fewer than {schema['minItems']} items")
        if "maxItems" in schema and len(data) > schema["maxItems"]:
            out.append(f"{at}: more than {schema['maxItems']} items")
        if "items" in schema:
            for i, item in enumerate(data):
                _check(schema["items"], item, f"{at}[{i}]", out)
    if isinstance(data, dict):
        out += [f'{at}: missing "{k}"' for k in schema.get("required", []) if k not in data]
        props = schema.get("properties") or {}
        for key, value in data.items():
            if key in props:
                _check(props[key], value, f"{at}.{key}", out)
            elif schema.get("additionalProperties") is False:
                out.append(f'{at}: unexpected "{key}"')


def validate(schema: dict, data) -> list[str]:
    refused = _check_schema(schema, "schema")
    if refused:
        return refused
    out: list[str] = []
    _check(schema, data, "$", out)
    return out
