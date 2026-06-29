import json
from typing import Any, Dict, List, Optional, Tuple

from app.redis_client import get_redis_client


CACHE_TTL_SECONDS = 3600

POPULAR_SEARCHES: List[Tuple[str, str, str]] = [
    ("NYC", "LON", "2024-10-01"),
    ("SFO", "LAX", "2024-10-05"),
    ("NYC", "PAR", "2024-10-03"),
]


def _build_search_key(origin: str, destination: str, date: str) -> str:
    return f"flights_search:{origin}:{destination}:{date}"


def get_cached_search_results(origin: str, destination: str, date: str) -> Optional[List[Dict[str, Any]]]:
    client = get_redis_client()
    key = _build_search_key(origin, destination, date)
    raw = client.get(key)
    if raw is None:
        return None
    return json.loads(raw)


def set_cached_search_results(origin: str, destination: str, date: str, results: List[Dict[str, Any]]) -> None:
    client = get_redis_client()
    key = _build_search_key(origin, destination, date)
    value = json.dumps(results)
    client.set(key, value, ex=CACHE_TTL_SECONDS)


def prewarm_popular_searches() -> None:
    from app.models.models import search_flights

    client = get_redis_client()
    pipe = client.pipeline()
    for origin, destination, date in POPULAR_SEARCHES:
        key = _build_search_key(origin, destination, date)
        existing = client.exists(key)
        if not existing:
            results = search_flights(origin, destination, date)
            as_dict = [flight.dict() for flight in results]
            value = json.dumps(as_dict)
            pipe.set(key, value, ex=CACHE_TTL_SECONDS)
    pipe.execute()


PRICE_ALERTS_KEY = "price_alerts"


def get_all_price_alerts() -> List[Dict[str, Any]]:
    client = get_redis_client()
    raw_list = client.lrange(PRICE_ALERTS_KEY, 0, -1)
    if not raw_list:
        return []
    return [json.loads(item) for item in raw_list]


def add_price_alert(alert: Dict[str, Any]) -> None:
    client = get_redis_client()
    serialized = json.dumps(alert)
    client.rpush(PRICE_ALERTS_KEY, serialized)
