"""Robot Framework MCP Server - Natural Language Test Automation Bridge."""

from robotmcp.attach.mcp_attach import McpAttach  # noqa: F401

# Expose Keywords from McpAttach at the package level

__all__ = ["McpAttach"]

from importlib import metadata


def _resolve_version() -> str:
    """兼容上游 ``rf-mcp`` 与二次开发包名 ``rf-mcp-enhanced``。"""
    for _name in ("rf-mcp-enhanced", "rf-mcp"):
        try:
            return metadata.version(_name)
        except metadata.PackageNotFoundError:
            continue
    return "0.0.0"


__version__ = _resolve_version()
