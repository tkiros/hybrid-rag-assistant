"""MCP server exposing `search` over stdio:  python -m app.mcp_server

Lets an MCP client (Claude Code, Claude Desktop ...) search the manuals and get back chunks
with doc/page citations. See the README for the client config.
"""

from typing import Literal

from mcp.server.mcpserver import MCPServer

from app import search as retrieval

mcp = MCPServer("kb-search")


@mcp.tool()
def search(query: str, mode: Literal["bm25", "vector", "hybrid"] = "hybrid",
           k: int = 5) -> list[dict]:
    """Search the Halvard compressor manual and warranty handbook.

    mode: bm25 (exact words and identifiers), vector (meaning) or hybrid (both, the default).
    Returns up to k chunks, best first, each with doc_id, page and section to cite.
    """
    k = max(1, min(k, 20))
    return [chunk.model_dump() for chunk in retrieval.search(query, mode, k)]


if __name__ == "__main__":
    mcp.run()
