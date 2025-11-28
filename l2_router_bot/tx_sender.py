"""Transaction signing and broadcasting utilities.

This module provides a small helper class used for building,
signing and sending Ether transfers on the configured Layer‑2
networks.  It should be used cautiously: sending transactions
without appropriate confirmation can result in irreversible loss of
funds.  Private keys must be provided via environment variables or
explicitly injected into the :class:`TransactionSender`.  Never
commit private keys to your source code or store them in this
repository.
"""

from __future__ import annotations

import os
from typing import Optional

from web3 import Web3  # type: ignore

from .networks import get_networks, get_web3_clients, NetworkConfig


class TransactionSender:
    """Helper for signing and sending transactions on Layer‑2 networks.

    Instantiate this class with a private key (or rely on the
    ``PRIVATE_KEY`` environment variable) to send Ether transfers.

    Args:
        private_key: Hex string representing the ECDSA private key.

    Raises:
        ValueError: If no private key is provided.
    """

    def __init__(self, private_key: Optional[str] = None) -> None:
        key = private_key or os.getenv("PRIVATE_KEY")
        if not key:
            raise ValueError(
                "A private key must be supplied either via the ``private_key`` "
                "parameter or the PRIVATE_KEY environment variable."
            )
        self.private_key = key

    def send_transfer(
        self,
        network_name: str,
        from_address: str,
        to_address: str,
        amount_wei: int,
    ) -> str:
        """Build, sign and broadcast a simple Ether transfer.

        Args:
            network_name: Name of the target network (e.g. "arbitrum").
            from_address: Hex-encoded sender address.
            to_address: Hex-encoded recipient address.
            amount_wei: Amount of Ether to transfer, denominated in wei.

        Returns:
            The transaction hash as a hex string.

        Raises:
            ValueError: If the network is unsupported or addresses are invalid.
            Exception: If the RPC request fails or transaction cannot be sent.
        """
        networks = get_networks()
        if network_name not in networks:
            raise ValueError(f"Unsupported network '{network_name}'.")
        cfg: NetworkConfig = networks[network_name]
        clients = get_web3_clients()
        w3: Web3 = clients[network_name]
        try:
            from_checksum = w3.to_checksum_address(from_address)
            to_checksum = w3.to_checksum_address(to_address)
        except Exception as exc:
            raise ValueError(f"Invalid address provided: {exc}") from exc
        nonce = w3.eth.get_transaction_count(from_checksum)
        gas_price = w3.eth.gas_price
        tx = {
            "chainId": cfg.chain_id,
            "to": to_checksum,
            "value": amount_wei,
            "nonce": nonce,
            "gasPrice": gas_price,
        }
        gas_limit = w3.eth.estimate_gas({
            "from": from_checksum,
            "to": to_checksum,
            "value": amount_wei,
        })
        tx["gas"] = gas_limit
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=self.private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return w3.to_hex(tx_hash)
