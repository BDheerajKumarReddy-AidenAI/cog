from typing import Any
from langchain_core.tools import tool
from sqlalchemy import text
from app.core.database import async_session_maker
import asyncio
import json


def run_async(coro):
    """Helper to run async code in sync context."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


async def execute_sql_async(query: str) -> dict[str, Any]:
    """Execute SQL query and return results."""
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
            return {"success": False, "error": str(e), "data": [], "row_count": 0}


@tool
def execute_sql_query(query: str) -> str:
    """
    Execute a SQL query against the PostgreSQL analytics database.
    Use this tool to fetch data for analysis, generate reports, or answer data-related questions.

    Args:
        query: A valid SQL SELECT query. Only SELECT queries are allowed for security.

    Returns:
        JSON string containing query results with columns and data rows.
    """
    query_upper = query.strip().upper()
    if not query_upper.startswith("SELECT"):
        return json.dumps(
            {"success": False, "error": "Only SELECT queries are allowed", "data": []}
        )

    result = run_async(execute_sql_async(query))
    return json.dumps(result, default=str)


@tool
def get_table_info(table_name: str) -> str:
    """
    Get information about a specific table including column names and sample data.

    Args:
        table_name: Name of the table (sales_data, customers, or products)

    Returns:
        JSON string with table structure and sample rows.
    """
    valid_tables = ["sales_data", "customers", "products"]
    if table_name not in valid_tables:
        return json.dumps(
            {"success": False, "error": f"Invalid table. Choose from: {valid_tables}"}
        )

    query = f"SELECT * FROM {table_name} LIMIT 5"
    result = run_async(execute_sql_async(query))
    return json.dumps(result, default=str)


@tool
def get_analytics_summary() -> str:
    """
    Get a high-level summary of the analytics database including record counts and date ranges.

    Returns:
        JSON string with database summary statistics.
    """
    queries = {
        "sales_count": "SELECT COUNT(*) as count FROM sales_data",
        "customer_count": "SELECT COUNT(*) as count FROM customers",
        "product_count": "SELECT COUNT(*) as count FROM products",
        "sales_date_range": "SELECT MIN(date) as min_date, MAX(date) as max_date FROM sales_data",
        "total_revenue": "SELECT SUM(total_amount) as total FROM sales_data",
        "regions": "SELECT DISTINCT region FROM sales_data",
        "segments": "SELECT DISTINCT segment FROM customers",
        "categories": "SELECT DISTINCT category FROM products",
    }

    summary = {}
    for key, query in queries.items():
        result = run_async(execute_sql_async(query))
        if result["success"] and result["data"]:
            summary[key] = result["data"][0] if len(result["data"]) == 1 else result["data"]

    return json.dumps({"success": True, "summary": summary}, default=str)


# List of all available tools for the agent
SQL_TOOLS = [execute_sql_query, get_table_info, get_analytics_summary]
