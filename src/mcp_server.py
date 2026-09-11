from src.sql_tool import execute_select

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover
    FastMCP = None


def build_server():
    if FastMCP is None:
        raise RuntimeError("Install mcp to run the SQL MCP server.")
    mcp = FastMCP("sql-sandbox")

    @mcp.tool()
    def execute_select_tool(sql: str) -> dict:
        """Run a SELECT-only SQL query on the music-store database."""
        return execute_select(sql)

    return mcp


def main() -> None:
    build_server().run()


if __name__ == "__main__":
    main()
