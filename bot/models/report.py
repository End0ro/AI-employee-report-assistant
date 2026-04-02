from datetime import datetime, timedelta
from bot.models.database import get_db


def get_current_week_start() -> str:
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    return monday.strftime("%Y-%m-%d")


async def save_report(
    employee_id: int,
    ads_posted: int,
    views: int,
    reach_outs: int,
    favorites: int,
    ad_spend: float,
) -> int:
    db = await get_db()
    try:
        week_start = get_current_week_start()
        await db.execute(
            "DELETE FROM reports WHERE employee_id = ? AND week_start = ?",
            (employee_id, week_start),
        )
        cursor = await db.execute(
            """INSERT INTO reports (employee_id, ads_posted, views, reach_outs, favorites, ad_spend, week_start)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (employee_id, ads_posted, views, reach_outs, favorites, ad_spend, week_start),
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def get_reports_for_week(week_start: str | None = None) -> list[dict]:
    if week_start is None:
        week_start = get_current_week_start()
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT r.*, e.full_name, e.username, e.telegram_id
               FROM reports r
               JOIN employees e ON r.employee_id = e.id
               WHERE r.week_start = ?
               ORDER BY r.submitted_at DESC""",
            (week_start,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def has_report_this_week(employee_id: int) -> bool:
    week_start = get_current_week_start()
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM reports WHERE employee_id = ? AND week_start = ?",
            (employee_id, week_start),
        )
        row = await cursor.fetchone()
        return row["cnt"] > 0
    finally:
        await db.close()


async def get_employees_without_report_this_week() -> list[dict]:
    week_start = get_current_week_start()
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT e.* FROM employees e
               WHERE e.id NOT IN (
                   SELECT employee_id FROM reports WHERE week_start = ?
               )""",
            (week_start,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()
