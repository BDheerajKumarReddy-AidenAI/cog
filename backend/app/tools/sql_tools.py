from typing import Any
from langchain_core.tools import tool
from sqlalchemy import text
from app.core.database import async_session_maker
import json
import logging

logger = logging.getLogger(__name__)


async def execute_sql_async(query: str) -> dict[str, Any]:
    """
    Execute a read-only SQL query asynchronously using SQLAlchemy AsyncSession.

    This function:
    - Opens an async database session
    - Executes the provided SQL query
    - Fetches all rows and converts them into a list of dictionaries

    Parameters
    ----------
    query : str
        A SQL SELECT query to execute.

    Returns
    -------
    dict[str, Any]
        A dictionary containing:
        - success (bool): Whether execution succeeded
        - data (list[dict]): Query result rows
        - row_count (int): Number of rows returned
        - columns (list[str]): Column names (on success)
        - error (str): Error message (on failure)
    """
    logger.info("Executing SQL query")

    async with async_session_maker() as session:
        try:
            result = await session.execute(text(query))
            rows = result.fetchall()
            columns = result.keys()

            data = [dict(zip(columns, row)) for row in rows]

            return {
                "success": True,
                "data": data,
                "row_count": len(data),
                "columns": list(columns),
            }

        except Exception as e:
            logger.exception("SQL execution failed")
            return {
                "success": False,
                "error": str(e),
                "data": [],
                "row_count": 0,
            }


@tool
async def execute_sql_query(query: str) -> str:
    """
    LangChain tool to execute a SELECT SQL query against the analytics database.

    Safety rules:
    - Only SELECT queries are allowed
    - Any non-SELECT query is rejected

    Parameters
    ----------
    query : str
        A SQL SELECT query.

    Returns
    -------
    str
        JSON string containing query results or an error message.
    """
    logger.info("execute_sql_query tool invoked")

    if not query.strip().upper().startswith("SELECT"):
        return json.dumps(
            {
                "success": False,
                "error": "Only SELECT queries are allowed",
                "data": [],
            }
        )

    result = await execute_sql_async(query)
    return json.dumps(result, default=str)


@tool
async def get_table_info(table_name: str) -> str:
    """
    LangChain tool to retrieve basic information and sample rows from a table.

    The tool:
    - Validates the table name against an allowlist
    - Fetches up to 5 rows from the table

    Parameters
    ----------
    table_name : str
        Name of the table to inspect.

    Returns
    -------
    str
        JSON string containing sample rows or an error message.
    """
    valid_tables = ["sales_data", "customers", "products"]

    if table_name not in valid_tables:
        return json.dumps(
            {
                "success": False,
                "error": f"Invalid table. Choose from: {valid_tables}",
            }
        )

    query = f"SELECT * FROM {table_name} LIMIT 5"
    result = await execute_sql_async(query)
    return json.dumps(result, default=str)


@tool
async def get_analytics_summary() -> str:
    """
    LangChain tool to generate a high-level analytics summary.

    This tool runs multiple aggregate queries to provide:
    - Total sales count
    - Total customer count
    - Total product count

    Returns
    -------
    str
        JSON string containing a summary of key analytics metrics.
    """
    queries = {
        "sales_count": "SELECT COUNT(*) as count FROM sales_data",
        "customer_count": "SELECT COUNT(*) as count FROM customers",
        "product_count": "SELECT COUNT(*) as count FROM products",
    }

    summary = {}

    for key, query in queries.items():
        result = await execute_sql_async(query)
        if result["success"] and result["data"]:
            summary[key] = result["data"][0]

    return json.dumps({"success": True, "summary": summary}, default=str)

# List of all available tools for the agent
SQL_TOOLS = [
    execute_sql_query,
    get_table_info,
    get_analytics_summary,
]
