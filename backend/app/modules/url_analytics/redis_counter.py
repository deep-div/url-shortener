import datetime
from app.clients.redis import redis_client
from app.modules.url_analytics.schema import LiveSnapshot, LiveSummary

# Key schema — mirrors app.modules.url_analytics.schema.UrlStatsResponse,
# the source-of-truth read schema for the analytics dashboard UI.
# stats:{code}:total_clicks        → string counter
# stats:{code}:last_clicked_at     → string ISO timestamp
# stats:{code}:by_country          → hash  {country: count}
# stats:{code}:by_city             → hash  {city: count}
# stats:{code}:by_device           → hash  {device: count}
# stats:{code}:by_browser          → hash  {browser: count}
# stats:{code}:clicks_by_day       → hash  {YYYY-MM-DD: count}

TTL_SECONDS = 60 * 60 * 24 * 7  # 7 days — evict stale URL counters automatically


def _keys(code: str) -> dict[str, str]:
    p = f"stats:{code}"
    return {
        "total_clicks":     f"{p}:total_clicks",
        "last_clicked_at":  f"{p}:last_clicked_at",
        "by_country":       f"{p}:by_country",
        "by_city":          f"{p}:by_city",
        "by_device":        f"{p}:by_device",
        "by_browser":       f"{p}:by_browser",
        "clicks_by_day":    f"{p}:clicks_by_day",
    }


async def increment_click(
    code: str,
    clicked_at: datetime.datetime,
    country: str | None,
    city: str | None,
    device: str | None,
    browser: str | None,
) -> None:
    k = _keys(code)
    date_str = clicked_at.strftime("%Y-%m-%d")
    clicked_at_iso = clicked_at.isoformat()

    pipe = redis_client.pipeline()

    pipe.incr(k["total_clicks"])
    pipe.set(k["last_clicked_at"], clicked_at_iso)
    pipe.hincrby(k["by_country"], country or "Others", 1)
    pipe.hincrby(k["by_city"], city or "Others", 1)
    pipe.hincrby(k["by_device"], device or "Others", 1)
    pipe.hincrby(k["by_browser"], browser or "Others", 1)
    pipe.hincrby(k["clicks_by_day"], date_str, 1)

    for key in k.values():
        pipe.expire(key, TTL_SECONDS)

    await pipe.execute()


async def seed_counters_if_missing(
    code: str,
    total_clicks: int,
    last_clicked_at: datetime.datetime | None,
    by_country: dict[str, int],
    by_city: dict[str, int],
    by_device: dict[str, int],
    by_browser: dict[str, int],
    clicks_by_day: dict[str, int],
) -> None:
    k = _keys(code)

    # SET NX is the atomic gate — if the key already exists, Kafka is already
    # live-incrementing this code and we must not clobber real-time counts.
    acquired = await redis_client.set(k["total_clicks"], total_clicks, nx=True)
    if not acquired:
        return

    pipe = redis_client.pipeline()
    if last_clicked_at:
        pipe.set(k["last_clicked_at"], last_clicked_at.isoformat())
    if by_country:
        pipe.hset(k["by_country"], mapping=by_country)
    if by_city:
        pipe.hset(k["by_city"], mapping=by_city)
    if by_device:
        pipe.hset(k["by_device"], mapping=by_device)
    if by_browser:
        pipe.hset(k["by_browser"], mapping=by_browser)
    if clicks_by_day:
        pipe.hset(k["clicks_by_day"], mapping=clicks_by_day)

    for key in k.values():
        pipe.expire(key, TTL_SECONDS)

    await pipe.execute()


async def get_live_stats(code: str) -> dict:
    k = _keys(code)

    pipe = redis_client.pipeline()
    pipe.get(k["total_clicks"])
    pipe.get(k["last_clicked_at"])
    pipe.hgetall(k["by_country"])
    pipe.hgetall(k["by_city"])
    pipe.hgetall(k["by_device"])
    pipe.hgetall(k["by_browser"])
    pipe.hgetall(k["clicks_by_day"])

    (
        total_clicks,
        last_clicked_at,
        by_country,
        by_city,
        by_device,
        by_browser,
        clicks_by_day,
    ) = await pipe.execute()

    by_country = {k: int(v) for k, v in by_country.items()}
    by_city = {k: int(v) for k, v in by_city.items()}
    by_device = {k: int(v) for k, v in by_device.items()}
    by_browser = {k: int(v) for k, v in by_browser.items()}

    return {
        "total_clicks":     int(total_clicks or 0),
        "last_clicked_at":  last_clicked_at,
        "by_country":       by_country,
        "by_city":          by_city,
        "by_device":        by_device,
        "by_browser":       by_browser,
        "clicks_by_day":    {k: int(v) for k, v in clicks_by_day.items()},
    }


async def get_live_snapshot(code: str) -> LiveSnapshot:
    """Live-update payload published over SSE — summary + breakdowns.

    Returns a validated `LiveSnapshot` (schema.py), the enforced source of
    truth for the Redis counters and the analytics dashboard's live updates.
    """
    stats = await get_live_stats(code)
    return LiveSnapshot(
        summary=LiveSummary(
            total_clicks=stats["total_clicks"],
            last_clicked_at=stats["last_clicked_at"],
            total_countries=len(stats["by_country"]),
            total_cities=len(stats["by_city"]),
        ),
        by_country=stats["by_country"],
        by_city=stats["by_city"],
        by_device=stats["by_device"],
        by_browser=stats["by_browser"],
        clicks_by_day=stats["clicks_by_day"],
    )
