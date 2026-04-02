from bot.models.database import get_db


async def create_employee(telegram_id: int, username: str | None, full_name: str):
    db = await get_db()
    try:
        await db.execute(
            "INSERT OR IGNORE INTO employees (telegram_id, username, full_name) VALUES (?, ?, ?)",
            (telegram_id, username, full_name),
        )
        await db.commit()
    finally:
        await db.close()


async def get_employee_by_telegram_id(telegram_id: int) -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM employees WHERE telegram_id = ?", (telegram_id,)
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        await db.close()


async def get_employee_by_id(employee_id: int) -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM employees WHERE id = ?", (employee_id,)
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        await db.close()


async def get_all_employees() -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM employees")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def delete_employee(employee_id: int) -> bool:
    db = await get_db()
    try:
        await db.execute("DELETE FROM reports WHERE employee_id = ?", (employee_id,))
        cursor = await db.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()
