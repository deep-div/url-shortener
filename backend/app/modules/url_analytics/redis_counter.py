import datetime
from app.clients.redis import redis_client

# Key schema
# stats:{code}:total_clicks        → string counter
# stats:{code}:clicks_today        → string counter  (resets daily)
# stats:{code}:clicks_this_week    → string counter  (resets weekly)
# stats:{code}:last_clicked_at     → string ISO timestamp
# stats:{code}:by_country          → hash  {country: count}
# stats:{code}:by_city             → hash  {city: count}
# stats:{code}:by_device           → hash  {device: count}
# stats:{code}:by_browser          → hash  {browser: count}
# stats:{code}:by_os               → hash  {os: count}
# stats:{code}:clicks_by_day       → hash  {YYYY-MM-DD: count}

TTL_SECONDS = 60 * 60 * 24 * 7  # 7 days — evict stale URL counters automatically


def _keys(code: str) -> dict[str, str]:
    p = f"stats:{code}"
    return {
        "total_clicks":     f"{p}:total_clicks",
        "clicks_today":     f"{p}:clicks_today",
        "clicks_this_week": f"{p}:clicks_this_week",
        "last_clicked_at":  f"{p}:last_clicked_at",
        "by_country":       f"{p}:by_country",
        "by_city":          f"{p}:by_city",
        "by_device":        f"{p}:by_device",
        "by_browser":       f"{p}:by_browser",
        "by_os":            f"{p}:by_os",
        "clicks_by_day":    f"{p}:clicks_by_day",
    }


async def increment_click(
    code: str,
    clicked_at: datetime.datetime,
    country: str | None,
    city: str | None,
    device: str | None,
    browser: str | None,
    os: str | None,
) -> None:
    k = _keys(code)
    date_str = clicked_at.strftime("%Y-%m-%d")
    clicked_at_iso = clicked_at.isoformat()

    pipe = redis_client.pipeline()

    pipe.incr(k["total_clicks"])
    pipe.incr(k["clicks_today"])
    pipe.incr(k["clicks_this_week"])
    pipe.set(k["last_clicked_at"], clicked_at_iso)
    pipe.hincrby(k["by_country"], country or "Others", 1)
    pipe.hincrby(k["by_city"], city or "Others", 1)
    pipe.hincrby(k["by_device"], device or "Others", 1)
    pipe.hincrby(k["by_browser"], browser or "Others", 1)
    pipe.hincrby(k["by_os"], os or "Others", 1)
    pipe.hincrby(k["clicks_by_day"], date_str, 1)

    for key in k.values():
        pipe.expire(key, TTL_SECONDS)

    await pipe.execute()


async def get_live_stats(code: str) -> dict:
    k = _keys(code)

    pipe = redis_client.pipeline()
    pipe.get(k["total_clicks"])
    pipe.get(k["clicks_today"])
    pipe.get(k["clicks_this_week"])
    pipe.get(k["last_clicked_at"])
    pipe.hgetall(k["by_country"])
    pipe.hgetall(k["by_city"])
    pipe.hgetall(k["by_device"])
    pipe.hgetall(k["by_browser"])
    pipe.hgetall(k["by_os"])
    pipe.hgetall(k["clicks_by_day"])

    (
        total_clicks,
        clicks_today,
        clicks_this_week,
        last_clicked_at,
        by_country,
        by_city,
        by_device,
        by_browser,
        by_os,
        clicks_by_day,
    ) = await pipe.execute()

    return {
        "total_clicks":     int(total_clicks or 0),
        "clicks_today":     int(clicks_today or 0),
        "clicks_this_week": int(clicks_this_week or 0),
        "last_clicked_at":  last_clicked_at,
        "by_country":       {k: int(v) for k, v in by_country.items()},
        "by_city":          {k: int(v) for k, v in by_city.items()},
        "by_device":        {k: int(v) for k, v in by_device.items()},
        "by_browser":       {k: int(v) for k, v in by_browser.items()},
        "by_os":            {k: int(v) for k, v in by_os.items()},
        "clicks_by_day":    {k: int(v) for k, v in clicks_by_day.items()},
    }
