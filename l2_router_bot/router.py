"""Gas comparison and route selection functions for Layer‑2 transfers.

This module encapsulates the logic for comparing the cost of sending
Ether across multiple Layer‑2 networks.  It exposes functions to
estimate transaction fees per network and to select the cheapest
option.  It is designed to be used both by the FastAPI endpoints
and programmatically from other modules.

The functions herein are asynchronous because price feeds may
involve network I/O.  Web3 calls are performed synchronously
because the underlying library does not yet support asyncio.  If
`web3.py` adds native async support in the future, these functions
can be refactored accordingly.
"""

from __future__ import annotations

from typing import Dict, Optional
from web3 import Web3  # type: ignore

from .networks import get_networks, get_web3_clients, NetworkConfig
from .utils.price_feed import get_token_price

async def estimate_transfer_costs(
    from_address: str,
    to_address: str,
    amount_wei: int,
    include_usd: bool = True,
) -> Dict[str, Dict[str, Optional[float]]]:
    """Estimate the cost of sending a transfer across all configured L2 networks."""
    networks: Dict[str, NetworkConfig] = get_networks()
    clients = get_web3_clients()
    results: Dict[str, Dict[str, Optional[float]]] = {}

    any_client: Web3 = next(iter(clients.values()))
    try:
        from_checksum = any_client.to_checksum_address(from_address)
        to_checksum = any_client.to_checksum_address(to_address)
    except Exception as exc:
        raise ValueError(f"Invalid address provided: {exc}") from exc

    for name, cfg in networks.items():
        w3: Web3 = clients[name]
        try:
            gas_price = w3.eth.gas_price
            nonce = w3.eth.get_transaction_count(from_checksum)
            tx = {
                "from": from_checksum,
                "to": to_checksum,
                "value": amount_wei,
                "nonce": nonce,
            }
            estimated_gas = w3.eth.estimate_gas(tx)
            total_fee_wei = gas_price * estimated_gas
            total_fee_native = Web3.from_wei(total_fee_wei, "ether")
            fee_usd: Optional[float] = None
            if include_usd:
                price = await get_token_price(cfg.native_symbol)
                if price is not None:
                    fee_usd = float(total_fee_native) * price
        except Exception as exc:
            results[name] = {"error": str(exc)}
            continue
        results[name] = {
            "gas_price_wei": int(gas_price),
            "estimated_gas": int(estimated_gas),
            "total_fee_wei": int(total_fee_wei),
            "total_fee_native": float(total_fee_native),
            "total_fee_usd": fee_usd,
        }
    return results


def select_cheapest_network(costs: Dict[str, Dict[str, Optional[float]]]) -> Optional[str]:
    """Select the network with the lowest estimated total fee in wei."""
    cheapest_name: Optional[str] = None
    cheapest_fee: Optional[int] = None
    for name, data in costs.items():
        if "error" in data:
            continue
        fee = data.get("total_fee_wei")
        if fee is None:
            continue
        if cheapest_fee is None or fee < cheapest_fee:
            cheapest_fee = fee
            cheapest_name = name
    return cheapest_name
