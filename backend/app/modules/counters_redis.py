from app.clients.redis import redis_client


def _key(code: str, bucket: str) -> str:
    return f"analytics:{code}:{bucket}"


async def is_populated(code: str) -> bool:
    return bool(await redis_client.exists(_key(code, "summary")))


async def populate_from_db(code: str, stats) -> None:
    """Cold start — load Postgres aggregates into Redis hashes."""
    pipe = redis_client.pipeline()

    pipe.hset(_key(code, "summary"), mapping={
        "total_clicks":   stats.summary.total_clicks,
        "unique_clicks":  stats.summary.unique_clicks,
        "last_clicked_at": stats.summary.last_clicked_at.isoformat() if stats.summary.last_clicked_at else "",
    })

    for bucket, data in [
        ("country", stats.by_country),
        ("city",    stats.by_city),
        ("device",  stats.by_device),
        ("browser", stats.by_browser),
    ]:
        if data:
            pipe.hset(_key(code, bucket), mapping=data)

    await pipe.execute()


async def increment_counters(code: str, click, is_unique: bool) -> None:
    """Increment Redis counters for one click — zero DB reads."""
    pipe = redis_client.pipeline()

    pipe.hincrby(_key(code, "summary"), "total_clicks", 1)
    if is_unique:
        pipe.hincrby(_key(code, "summary"), "unique_clicks", 1)
    pipe.hset(_key(code, "summary"), "last_clicked_at", click.clicked_at.isoformat())

    if click.country:
        pipe.hincrby(_key(code, "country"), click.country, 1)
    if click.city:
        pipe.hincrby(_key(code, "city"), click.city, 1)
    if click.device:
        pipe.hincrby(_key(code, "device"), str(click.device.value), 1)
    if click.browser:
        pipe.hincrby(_key(code, "browser"), click.browser, 1)

    await pipe.execute()


async def get_snapshot(code: str) -> dict:
    """Read Redis hashes and build the live snapshot dict."""
    pipe = redis_client.pipeline()
    pipe.hgetall(_key(code, "summary"))
    pipe.hgetall(_key(code, "country"))
    pipe.hgetall(_key(code, "city"))
    pipe.hgetall(_key(code, "device"))
    pipe.hgetall(_key(code, "browser"))

    summary_raw, country, city, device, browser = await pipe.execute()

    return {
        "summary": {
            "total_clicks":    int(summary_raw.get("total_clicks", 0)),
            "unique_clicks":   int(summary_raw.get("unique_clicks", 0)),
            "total_countries": len(country),
            "total_cities":    len(city),
            "last_clicked_at": summary_raw.get("last_clicked_at") or None,
        },
        "by_country": {k: int(v) for k, v in country.items()},
        "by_city":    {k: int(v) for k, v in city.items()},
        "by_device":  {k: int(v) for k, v in device.items()},
        "by_browser": {k: int(v) for k, v in browser.items()},
    }
