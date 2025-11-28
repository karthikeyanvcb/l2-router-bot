"""Simple price feed for retrieving USD quotes for native tokens.

This module defines a helper to fetch the current USD price for
Ethereum and related tokens using the public CoinGecko API.  The
function is asynchronous and utilises the `httpx` library to
perform HTTP requests.  Should the request fail or a token not be
available, the function returns ``None``.  In production
deployments you may wish to cache results to avoid repeatedly
calling the external API and to handle API rate limits.
"""

from __future__ import annotations

from typing import Optional

import httpx  # type: ignore


# Mapping from native token symbols to CoinGecko IDs.  Extend this
# dictionary when adding support for tokens beyond Ether on L2
# networks.
TOKEN_ID_MAP = {
    "ETH": "ethereum",
}


async def get_token_price(symbol: str) -> Optional[float]:
    """Retrieve the current USD price for a given native token symbol.

    Args:
        symbol: Ticker symbol for the native token (e.g. ``"ETH"``).

    Returns:
        The current price in USD, or ``None`` if the symbol is
        unsupported or the request fails.
    """

    token_id = TOKEN_ID_MAP.get(symbol.upper())
    if token_id is None:
        return None
    url = (
        "https://api.coingecko.com/api/v3/simple/price?"
        f"ids={token_id}&vs_currencies=usd"
    )
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            price = data.get(token_id, {}).get("usd")
            return float(price) if price is not None else None
    except Exception:
        # On any error (network, JSON parsing, missing key) return None
        return None
