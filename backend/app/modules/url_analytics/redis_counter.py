import datetime
from app.clients.redis import redis_client
from app.modules.url_analytics.schema import (
    UrlStatsResponse, LinkInfo, SummaryInfo, ClicksByDayItem,
)

TTL_SECONDS = 60 * 60 * 24 * 7  # 7 days — evict stale URL counters automatically


def _keys(code: str) -> dict[str, str]:
    p = f"stats:{code}"
    return {
        "link":             f"{p}:link",
        "total_clicks":     f"{p}:total_clicks",
        "unique_clicks":    f"{p}:unique_clicks",
        "last_clicked_at":  f"{p}:last_clicked_at",
        "by_country":       f"{p}:by_country",
        "by_city":          f"{p}:by_city",
        "by_device":        f"{p}:by_device",
        "by_browser":       f"{p}:by_browser",
        "clicks_by_day":    f"{p}:clicks_by_day",
        "peak_hours":       f"{p}:peak_hours",
    }


def _queue_click_increment(
    pipe,
    code: str,
    clicked_at: datetime.datetime,
    ip: str | None,
    country: str | None,
    city: str | None,
    device: str | None,
    browser: str | None,
) -> None:
    k = _keys(code)
    date_str = clicked_at.strftime("%Y-%m-%d")
    clicked_at_iso = clicked_at.isoformat()

    pipe.incr(k["total_clicks"])
    pipe.set(k["last_clicked_at"], clicked_at_iso)
    if ip:
        pipe.pfadd(k["unique_clicks"], ip)
    pipe.hincrby(k["by_country"], country or "Others", 1)
    pipe.hincrby(k["by_city"], city or "Others", 1)
    pipe.hincrby(k["by_device"], device or "Others", 1)
    pipe.hincrby(k["by_browser"], browser or "Others", 1)
    pipe.hincrby(k["clicks_by_day"], date_str, 1)
    pipe.hincrby(k["peak_hours"], str(clicked_at.hour), 1)


async def increment_clicks_batch(clicks: list) -> None:
    """Queues every click in `clicks` onto a single pipeline and executes it
    once — avoids checking out one Redis connection per click, which
    exhausts the connection pool on large batches.

    TTL is refreshed once per unique code per batch, not once per click —
    the same code clicked thousands of times in one batch only needs its
    keys' 7-day TTL restated once, not thousands of times."""
    if not clicks:
        return
    pipe = redis_client.pipeline()
    for c in clicks:
        _queue_click_increment(
            pipe,
            code=c.code,
            clicked_at=c.clicked_at,
            ip=c.ip,
            country=c.country,
            city=c.city,
            device=c.device.value if c.device else None,
            browser=c.browser,
        )
    for code in {c.code for c in clicks}:
        for key in _keys(code).values():
            pipe.expire(key, TTL_SECONDS)
    await pipe.execute()


# Cache-aside for the analytics dashboard (UrlStatsResponse) — Redis holds
# hot data for 7 days, Postgres remains the source of truth. A code is only
# considered "cached" when every key below is present; a single missing key
# means the whole dataset gets rebuilt from the DB.

async def cache_exists(code: str) -> bool:
    k = _keys(code)
    present = await redis_client.exists(*k.values())
    return present == len(k)


async def get_cached_stats(code: str) -> UrlStatsResponse:
    k = _keys(code)

    pipe = redis_client.pipeline()
    pipe.hgetall(k["link"])
    pipe.get(k["total_clicks"])
    pipe.pfcount(k["unique_clicks"])
    pipe.get(k["last_clicked_at"])
    pipe.hgetall(k["by_country"])
    pipe.hgetall(k["by_city"])
    pipe.hgetall(k["by_device"])
    pipe.hgetall(k["by_browser"])
    pipe.hgetall(k["clicks_by_day"])
    pipe.hgetall(k["peak_hours"])

    (
        link,
        total_clicks,
        unique_clicks,
        last_clicked_at,
        by_country,
        by_city,
        by_device,
        by_browser,
        clicks_by_day,
        peak_hours,
    ) = await pipe.execute()

    by_country = {c: int(v) for c, v in by_country.items()}
    by_city = {c: int(v) for c, v in by_city.items()}
    sort_desc = lambda d: dict(sorted(d.items(), key=lambda x: -x[1]))

    return UrlStatsResponse(
        link=LinkInfo(code=code, short_url=link["short_url"], long_url=link["long_url"]),
        summary=SummaryInfo(
            total_clicks=int(total_clicks or 0),
            unique_clicks=int(unique_clicks or 0),
            total_countries=len(by_country),
            total_cities=len(by_city),
            last_clicked_at=datetime.datetime.fromisoformat(last_clicked_at) if last_clicked_at else None,
        ),
        clicks_by_day=[
            ClicksByDayItem(date=d, clicks=int(c))
            for d, c in sorted(clicks_by_day.items())
        ],
        peak_hours={int(h): int(v) for h, v in peak_hours.items()},
        by_country=sort_desc(by_country),
        by_city=sort_desc(by_city),
        by_device=sort_desc({c: int(v) for c, v in by_device.items()}),
        by_browser=sort_desc({c: int(v) for c, v in by_browser.items()}),
    )


async def set_cached_stats(code: str, response: UrlStatsResponse, unique_ips: list[str]) -> None:
    """Seeds every stats:{code}:* key from a fully-built UrlStatsResponse.
    `unique_ips` is the exact IP list from Postgres's unique_ips table —
    it's only ever used here to build the stats:{code}:unique_clicks sketch and is
    never stored as-is or returned to the API."""
    k = _keys(code)
    pipe = redis_client.pipeline()

    pipe.hset(k["link"], mapping={"short_url": response.link.short_url, "long_url": response.link.long_url})
    pipe.set(k["total_clicks"], response.summary.total_clicks)
    if unique_ips:
        pipe.pfadd(k["unique_clicks"], *unique_ips)
    if response.summary.last_clicked_at:
        pipe.set(k["last_clicked_at"], response.summary.last_clicked_at.isoformat())
    if response.by_country:
        pipe.hset(k["by_country"], mapping=response.by_country)
    if response.by_city:
        pipe.hset(k["by_city"], mapping=response.by_city)
    if response.by_device:
        pipe.hset(k["by_device"], mapping=response.by_device)
    if response.by_browser:
        pipe.hset(k["by_browser"], mapping=response.by_browser)
    if response.clicks_by_day:
        pipe.hset(k["clicks_by_day"], mapping={item.date: item.clicks for item in response.clicks_by_day})
    if response.peak_hours:
        pipe.hset(k["peak_hours"], mapping=response.peak_hours)

    for key in k.values():
        pipe.expire(key, TTL_SECONDS)

    await pipe.execute()


async def get_live_snapshot(code: str) -> UrlStatsResponse:
    """Live-update payload published over SSE after every click. Now the
    exact same shape as the dashboard's GET response (UrlStatsResponse) —
    once increment_clicks_batch has run, Redis holds the full up-to-date picture,
    so this just re-reads the cache."""
    return await get_cached_stats(code)
