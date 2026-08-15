import sqlite3
from pathlib import Path
from typing import Any, Dict, List


DB_PATH = Path("data/operations.db")


def initialize_database() -> None:
    """Create the demo database and seed it if needed."""

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                category TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL
            )
            """
        )

        cursor.execute("SELECT COUNT(*) FROM inventory")
        row_count = cursor.fetchone()[0]

        if row_count == 0:
            sample_rows = [
                ("Laptop", "Electronics", 12, 1299.99),
                ("Monitor", "Electronics", 25, 349.50),
                ("Keyboard", "Electronics", 40, 89.99),
                ("Office Chair", "Furniture", 8, 499.00),
                ("Desk", "Furniture", 6, 799.00),
                ("Notebook", "Office Supplies", 120, 4.99),
                ("Pen Set", "Office Supplies", 75, 12.50),
            ]

            cursor.executemany(
                """
                INSERT INTO inventory (
                    item_name,
                    category,
                    quantity,
                    unit_price
                )
                VALUES (?, ?, ?, ?)
                """,
                sample_rows,
            )

        conn.commit()


def search_inventory(
    item_name: str = "",
    category: str = "",
) -> Dict[str, Any]:
    """
    Search inventory using optional item name and category filters.

    This tool exposes a constrained query interface rather than allowing
    arbitrary SQL execution.
    """

    initialize_database()

    query = """
        SELECT
            id,
            item_name,
            category,
            quantity,
            unit_price
        FROM inventory
        WHERE 1 = 1
    """

    parameters: List[Any] = []

    if item_name:
        query += " AND LOWER(item_name) LIKE LOWER(?)"
        parameters.append(f"%{item_name.strip()}%")

    if category:
        query += " AND LOWER(category) = LOWER(?)"
        parameters.append(category.strip())

    query += " ORDER BY item_name"

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(query, parameters)
        rows = [dict(row) for row in cursor.fetchall()]

    return {
        "filters": {
            "item_name": item_name,
            "category": category,
        },
        "count": len(rows),
        "items": rows,
    }