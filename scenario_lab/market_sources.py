"""Forecasting-market sources for event anchors: URL recognition and snapshots.

An event in ``events.md`` may carry a silent market anchor: ``**Market:**``
(or ``**Metaculus:**`` / ``**Manifold:**`` / ``**Polymarket:**``) holding a
question URL, ``**Retrieved:**`` the snapshot date, and ``**Market
probability:**`` the figure at that date. Anchors are for the people building
a scenario -- they are never rendered into a prompt and never fetched during a
run. This module is the authoring-time half: it recognises which platform a
URL belongs to and, where the platform has a public read API, fetches the
current figure so the author (or the update skill) can snapshot it.

Sources:

- **Manifold** -- public API, no key. Binary markets only.
- **Polymarket** -- public Gamma API, no key. A market with Yes/No outcomes;
  a multi-market event needs the URL of the specific market.
- **Metaculus** -- recognised and validated, but not fetched: its API
  needs an account token, so the figure is recorded by hand.

Nothing here judges what a figure means. Market odds are unconditional and
tied to a resolution date, while scenario events are conditional on the
simulated world and priced per turn.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Callable, Optional

SOURCE_METACULUS = "metaculus"
SOURCE_MANIFOLD = "manifold"
SOURCE_POLYMARKET = "polymarket"
SOURCES = (SOURCE_METACULUS, SOURCE_MANIFOLD, SOURCE_POLYMARKET)

# What the URL of each source must look like, for validation messages.
URL_SHAPES = {
    SOURCE_METACULUS: "https://www.metaculus.com/questions/<id>/<slug>/",
    SOURCE_MANIFOLD: "https://manifold.markets/<user>/<slug>",
    SOURCE_POLYMARKET: "https://polymarket.com/event/<event>/<market>",
}

MANIFOLD_API = "https://api.manifold.markets/v0"
POLYMARKET_API = "https://gamma-api.polymarket.com"

HttpGet = Callable[[str], Any]


class MarketError(ValueError):
    """A question could not be recognised or its figure could not be read."""


@dataclass
class MarketQuote:
    """One snapshot of a market question, ready to paste into ``events.md``."""

    source: str
    url: str
    title: str
    probability: float  # 0-1
    retrieved: str  # YYYY-MM-DD
    closes: Optional[str] = None  # resolution/close date, YYYY-MM-DD, when known

    @property
    def figure(self) -> str:
        """The figure as written in ``**Market probability:**``."""
        percent = self.probability * 100
        text = f"{percent:.1f}".rstrip("0").rstrip(".")
        return f"{text}%"


def _path_parts(url: str) -> list[str]:
    return [part for part in urllib.parse.urlparse(url).path.split("/") if part]


def _host(url: str) -> str:
    host = (urllib.parse.urlparse(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def detect_source(url: str) -> Optional[str]:
    """Which supported platform a question URL belongs to, or None."""
    host = _host(url)
    parts = _path_parts(url)
    if host == "metaculus.com" and len(parts) >= 2 and parts[0] == "questions":
        return SOURCE_METACULUS
    if host == "manifold.markets" and len(parts) >= 2:
        return SOURCE_MANIFOLD
    if host == "polymarket.com" and len(parts) >= 2 and parts[0] in ("event", "market"):
        return SOURCE_POLYMARKET
    return None


def check_url(url: str) -> Optional[str]:
    """Why a market URL is unusable, or None when it is recognised."""
    if detect_source(url) is not None:
        return None
    shapes = "; ".join(f"{name}: {shape}" for name, shape in URL_SHAPES.items())
    return f"'{url}' is not a recognised market question URL ({shapes})"


def default_http_get(url: str) -> Any:
    """GET a JSON document (stdlib only; short timeout; identifying agent)."""
    request = urllib.request.Request(
        url, headers={"User-Agent": "scenario-lab/5 (market anchors)", "Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        raise MarketError(f"{url}: HTTP {err.code}") from err
    except (urllib.error.URLError, TimeoutError, ValueError) as err:
        raise MarketError(f"{url}: {err}") from err


def _today() -> str:
    return date.today().isoformat()


def _from_millis(value: Any) -> Optional[str]:
    if isinstance(value, (int, float)) and value > 0:
        return datetime.fromtimestamp(value / 1000, tz=timezone.utc).date().isoformat()
    return None


def _from_iso(value: Any) -> Optional[str]:
    if isinstance(value, str) and re.match(r"\d{4}-\d{2}-\d{2}", value):
        return value[:10]
    return None


def fetch_manifold(url: str, http_get: HttpGet = default_http_get) -> MarketQuote:
    parts = _path_parts(url)
    slug = parts[-1]
    data = http_get(f"{MANIFOLD_API}/slug/{urllib.parse.quote(slug)}")
    if not isinstance(data, dict):
        raise MarketError(f"{url}: unexpected Manifold response")
    if data.get("outcomeType") != "BINARY":
        raise MarketError(
            f"{url}: Manifold market is {data.get('outcomeType')}, not BINARY. "
            "Anchor an event to a yes/no question."
        )
    probability = data.get("probability")
    if not isinstance(probability, (int, float)):
        raise MarketError(f"{url}: Manifold response carries no probability")
    return MarketQuote(
        source=SOURCE_MANIFOLD,
        url=url,
        title=str(data.get("question") or slug),
        probability=float(probability),
        retrieved=_today(),
        closes=_from_millis(data.get("closeTime")),
    )


def _yes_price(market: dict, url: str) -> float:
    try:
        outcomes = json.loads(market["outcomes"]) if isinstance(market.get("outcomes"), str) else market.get("outcomes")
        prices = json.loads(market["outcomePrices"]) if isinstance(market.get("outcomePrices"), str) else market.get("outcomePrices")
    except (KeyError, ValueError) as err:
        raise MarketError(f"{url}: Polymarket market has no readable prices") from err
    if not isinstance(outcomes, list) or not isinstance(prices, list) or len(outcomes) != len(prices):
        raise MarketError(f"{url}: Polymarket market has no readable prices")
    labels = [str(o).strip().lower() for o in outcomes]
    if "yes" not in labels or "no" not in labels:
        raise MarketError(
            f"{url}: Polymarket market outcomes are {outcomes}, not Yes/No. "
            "Anchor an event to a yes/no question."
        )
    try:
        return float(prices[labels.index("yes")])
    except (TypeError, ValueError) as err:
        raise MarketError(f"{url}: Polymarket price is not a number") from err


def fetch_polymarket(url: str, http_get: HttpGet = default_http_get) -> MarketQuote:
    parts = _path_parts(url)
    slug = parts[-1]
    markets = http_get(f"{POLYMARKET_API}/markets?slug={urllib.parse.quote(slug)}")
    market: Optional[dict] = None
    if isinstance(markets, list) and markets and isinstance(markets[0], dict):
        market = markets[0]
    else:
        # The URL may name an event rather than one of its markets.
        events = http_get(f"{POLYMARKET_API}/events?slug={urllib.parse.quote(slug)}")
        event = events[0] if isinstance(events, list) and events and isinstance(events[0], dict) else None
        if event is None:
            raise MarketError(f"{url}: Polymarket knows no market or event '{slug}'")
        members = [m for m in event.get("markets") or [] if isinstance(m, dict)]
        if len(members) != 1:
            slugs = ", ".join(str(m.get("slug")) for m in members[:5])
            raise MarketError(
                f"{url}: this Polymarket event holds {len(members)} markets; "
                f"use the URL of one of them (https://polymarket.com/event/{slug}/<market>), "
                f"e.g. {slugs}"
            )
        market = members[0]
    return MarketQuote(
        source=SOURCE_POLYMARKET,
        url=url,
        title=str(market.get("question") or slug),
        probability=_yes_price(market, url),
        retrieved=_today(),
        closes=_from_iso(market.get("endDate")),
    )


def fetch_quote(url: str, http_get: HttpGet = default_http_get) -> MarketQuote:
    """Fetch the current figure for a question URL.

    Raises:
        MarketError: Unrecognised URL, a platform without a public API
            (Metaculus), an unsupported question type, or a failed request.
    """
    source = detect_source(url)
    if source is None:
        raise MarketError(check_url(url) or url)
    if source == SOURCE_MANIFOLD:
        return fetch_manifold(url, http_get)
    if source == SOURCE_POLYMARKET:
        return fetch_polymarket(url, http_get)
    raise MarketError(
        f"{url}: Metaculus's API needs an account token, so its figure is not "
        "fetched here. Read the community prediction on the page and record it "
        "by hand under **Market probability:**."
    )


def format_quote(quote: MarketQuote) -> str:
    """The quote as lines ready to paste into an event block in ``events.md``."""
    lines = [
        f"{quote.title}",
        f"  **Market:** {quote.url}",
        f"  **Retrieved:** {quote.retrieved}",
        f"  **Market probability:** {quote.figure}",
    ]
    if quote.closes:
        lines.append(f"  (resolves/closes {quote.closes}: market odds are unconditional and "
                     "dated, the event is priced per turn)")
    return "\n".join(lines)
