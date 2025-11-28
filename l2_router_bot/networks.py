"""Configuration and client utilities for supported Layer‑2 networks.

This module defines immutable network configurations and helper
functions to produce :class:`web3.Web3` clients for each supported
network.  RPC endpoints can be overridden using environment
variables named ``ARBITRUM_RPC_URL``, ``OPTIMISM_RPC_URL`` and
``BASE_RPC_URL`` respectively.  Additional networks can be added by
extending the ``DEFAULT_NETWORKS`` dictionary.

All network definitions include the chain ID and the native token
symbol.  These values are used when building and signing
transactions.  If you wish to add support for a new network, be
sure to consult the network's documentation for the correct chain
identifier.

This module contains no side effects on import and is safe to
import from any context.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict

from web3 import Web3  # type: ignore


@dataclass(frozen=True)
class NetworkConfig:
    """Immutable configuration for a single Layer‑2 network.

    Args:
        name: Machine‑readable name for the network (e.g. ``arbitrum``).
        rpc_url: JSON‑RPC endpoint for the network.
        chain_id: Integer chain identifier as defined by EIP‑155.
        native_symbol: Symbol for the native currency (e.g. ``ETH``).
    """

    name: str
    rpc_url: str
    chain_id: int
    native_symbol: str


# Default network definitions.  Feel free to extend this dictionary
# with additional networks (e.g. zkSync Era) as required by your
# application.  RPC URLs may be overridden via environment variables.
DEFAULT_NETWORKS: Dict[str, NetworkConfig] = {
    "arbitrum": NetworkConfig(
        name="arbitrum",
        rpc_url="https://arb1.arbitrum.io/rpc",
        chain_id=42161,
        native_symbol="ETH",
    ),
    "optimism": NetworkConfig(
        name="optimism",
        rpc_url="https://mainnet.optimism.io",
        chain_id=10,
        native_symbol="ETH",
    ),
    "base": NetworkConfig(
        name="base",
        rpc_url="https://mainnet.base.org",
        chain_id=8453,
        native_symbol="ETH",
    ),
}


def get_networks() -> Dict[str, NetworkConfig]:
    """Return a mapping of supported network names to their configurations.

    Environment variables named ``ARBITRUM_RPC_URL``, ``OPTIMISM_RPC_URL`` and
    ``BASE_RPC_URL`` can be used to override the default RPC endpoints for
    their respective networks.  Additional networks can be configured by
    extending the :data:`DEFAULT_NETWORKS` dictionary.

    Returns:
        A dictionary keyed by network name containing :class:`NetworkConfig`
        instances.
    """

    networks: Dict[str, NetworkConfig] = {}
    for name, cfg in DEFAULT_NETWORKS.items():
        # Derive environment variable name from network name, e.g.
        # "arbitrum" -> "ARBITRUM_RPC_URL"
        env_var = f"{name.upper()}_RPC_URL"
        rpc_override = os.getenv(env_var)
        if rpc_override:
            networks[name] = NetworkConfig(
                name=cfg.name,
                rpc_url=rpc_override,
                chain_id=cfg.chain_id,
                native_symbol=cfg.native_symbol,
            )
        else:
            networks[name] = cfg
    return networks


def get_web3_clients() -> Dict[str, Web3]:
    """Instantiate a :class:`web3.Web3` client for each configured network.

    This helper caches nothing; it simply creates a new Web3 instance
    for each configured network.  If you plan to perform many RPC
    operations, you may wish to memoise this function at a higher
    layer of your application.

    Returns:
        A dictionary mapping network names to instantiated Web3 clients.
    """

    clients: Dict[str, Web3] = {}
    for name, cfg in get_networks().items():
        # Use HTTP provider; applications requiring higher throughput may
        # prefer WebSocket providers.
        clients[name] = Web3(Web3.HTTPProvider(cfg.rpc_url))
    return clients
