"""The MCP server, launched over stdio exactly as an MCP client would. Needs the database."""

import asyncio
import os
import sys

from mcp import Client
from mcp.client.stdio import StdioServerParameters

from evals.run import load
from tests.helpers import needs_chunks

pytestmark = needs_chunks


async def list_and_call(query: str):
    server = StdioServerParameters(command=sys.executable, args=["-m", "app.mcp_server"],
                                   env=dict(os.environ))
    async with Client(server) as client:
        tools = await client.list_tools()
        result = await client.call_tool("search", {"query": query, "mode": "hybrid", "k": 3})
    return tools, result


def test_mcp_client_lists_and_calls_search():
    row = next(r for r in load("dev", None) if r["type"] == "exact_id")
    tools, result = asyncio.run(list_and_call(row["question"]))

    (tool,) = tools.tools
    assert tool.name == "search"
    assert tool.input_schema["properties"]["mode"]["enum"] == ["bm25", "vector", "hybrid"]
    assert not result.is_error
    chunks = result.structured_content["result"]
    assert len(chunks) == 3
    assert {"chunk_id", "doc_id", "page", "section", "text"} <= set(chunks[0])
    needle = row["gold_needles"][0]
    assert any(needle in " ".join(c["text"].split()) for c in chunks)
