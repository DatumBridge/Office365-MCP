"""Copy each tool's Capabilities line and registry docs onto the input schema.

The Tool Registry reads x-datumbridge-capabilities and x-datumbridge-docs from
tools/list. A server-wide catalog list is not used when the capabilities key is
present. x-datumbridge-docs is the markdown in registry_docs/<tool>.md. Setup
and publish copy it onto the tool Docs field and drop it from the stored schema.
"""

from __future__ import annotations

from pathlib import Path

_REGISTRY_DOCS = Path(__file__).resolve().parents[1] / "registry_docs"
_MAX_DOCS = 24000


def capabilities_from_description(description: str) -> list[str]:
    for line in (description or "").splitlines():
        line = line.strip()
        if line.lower().startswith("capabilities:"):
            rest = line.split(":", 1)[1]
            return [part.strip() for part in rest.split(",") if part.strip()]
    return []


def registry_docs(name: str) -> str:
    safe = (name or "").strip()
    if not safe or "/" in safe or "\\" in safe or ".." in safe:
        return ""
    path = _REGISTRY_DOCS / f"{safe}.md"
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8").strip()
    if len(text) > _MAX_DOCS:
        text = text[:_MAX_DOCS]
    return text


def bind_declared_capabilities(mcp) -> None:
    manager = getattr(mcp, "_tool_manager", None)
    tools = getattr(manager, "_tools", None) or {}
    for tool in tools.values():
        name = getattr(tool, "name", "") or "tool"
        caps = capabilities_from_description(getattr(tool, "description", "") or "")
        if not caps:
            caps = [name]
        params = dict(getattr(tool, "parameters", None) or {})
        params["x-datumbridge-capabilities"] = caps
        docs = registry_docs(name)
        if docs:
            params["x-datumbridge-docs"] = docs
        tool.parameters = params

def build_register_manifest(
    mcp,
    *,
    server_id: str,
    name: str,
    version: str = "1.0.0",
) -> dict:
    """GET /register body: same tools[] shape as tools/list (remote gateway)."""
    manager = getattr(mcp, "_tool_manager", None)
    tools = getattr(manager, "_tools", None) or {}
    out = []
    for tool in tools.values():
        tool_name = (getattr(tool, "name", None) or "").strip()
        if not tool_name:
            continue
        params = dict(getattr(tool, "parameters", None) or {})
        if "type" not in params:
            params = {"type": "object", **params}
        out.append(
            {
                "name": tool_name,
                "description": getattr(tool, "description", "") or "",
                "inputSchema": params,
            }
        )
    out.sort(key=lambda t: t["name"])
    return {
        "server_id": server_id,
        "name": name,
        "version": version,
        "tools": out,
    }
