def format_report(report: dict) -> str:
    return (
        f"📊 <b>Отчёт от {report['full_name']}</b>\n"
        f"(@{report['username'] or 'нет username'})\n\n"
        f"📅 Неделя с {report['week_start']}\n\n"
        f"📌 Размещено объявлений: <b>{report['ads_posted']}</b>\n"
        f"👁 Просмотры: <b>{report['views']}</b>\n"
        f"📩 Обращения: <b>{report['reach_outs']}</b>\n"
        f"⭐️ В избранном: <b>{report['favorites']}</b>\n"
        f"💰 Расходы на продвижение: <b>{report['ad_spend']:.2f} ₽</b>\n\n"
        f"🕐 Отправлен: {report['submitted_at']}"
    )


def format_report_summary(reports: list[dict]) -> str:
    if not reports:
        return "📭 За эту неделю отчётов пока нет."

    lines = [f"📊 <b>Отчёты за неделю с {reports[0]['week_start']}</b>\n"]

    for r in reports:
        lines.append(
            f"👤 <b>{r['full_name']}</b> (@{r['username'] or '—'})\n"
            f"   📌 Объявлений: {r['ads_posted']}  |  "
            f"👁 Просмотры: {r['views']}  |  "
            f"📩 Обращения: {r['reach_outs']}\n"
            f"   ⭐️ Избранное: {r['favorites']}  |  "
            f"💰 Расходы: {r['ad_spend']:.2f} ₽\n"
        )

    return "\n".join(lines)


def format_employee_list(employees: list[dict]) -> str:
    if not employees:
        return "📭 Нет зарегистрированных сотрудников."

    lines = ["👥 <b>Список сотрудников:</b>\n"]
    for i, e in enumerate(employees, 1):
        lines.append(
            f"{i}. {e['full_name']} (@{e['username'] or '—'}) — ID: {e['telegram_id']}"
        )
    return "\n".join(lines)
