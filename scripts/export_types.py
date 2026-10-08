"""Generate TypeScript aliases for every FastAPI OpenAPI component schema."""

from pathlib import Path

from aquasentinel.main import app


def ts_type(schema: dict) -> str:
    if "$ref" in schema:
        return schema["$ref"].split("/")[-1]
    if "anyOf" in schema:
        return " | ".join(ts_type(item) for item in schema["anyOf"])
    if "allOf" in schema:
        return " & ".join(ts_type(item) for item in schema["allOf"])
    if "enum" in schema:
        return " | ".join(repr(item).replace("'", '"') for item in schema["enum"])
    kind = schema.get("type")
    if kind == "array":
        return f"Array<{ts_type(schema.get('items', {}))}>"
    if kind == "object":
        properties = schema.get("properties")
        if properties:
            required = set(schema.get("required", []))
            fields = [f"{name}{'' if name in required else '?'}: {ts_type(value)};" for name, value in properties.items()]
            return "{ " + " ".join(fields) + " }"
        return "Record<string, unknown>"
    if kind in {"number", "integer"}:
        return "number"
    if kind == "boolean":
        return "boolean"
    if kind == "null":
        return "null"
    if kind == "string":
        return "string"
    return "unknown"


def main() -> None:
    schemas = app.openapi()["components"]["schemas"]
    lines = ["// Generated from the verified FastAPI OpenAPI schema. Do not edit by hand."]
    lines.extend(f"export type {name} = {ts_type(schema)};" for name, schema in sorted(schemas.items()))
    destination = Path(__file__).resolve().parents[1] / "contracts" / "generated.ts"
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(destination)


if __name__ == "__main__":
    main()
