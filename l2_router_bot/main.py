"""FastAPI application for the L2 Router Bot package.

This file defines a FastAPI application that exposes endpoints for
retrieving network information, estimating transfer costs, selecting
the cheapest network and broadcasting transactions.  It also
includes a simple route to serve a static HTML dashboard.  The
application is designed to be self‑contained and can be run via
Uvicorn using ``uvicorn l2_router_bot.main:app``.
"""

from __future__ import annotations

import os
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from web3 import Web3  # type: ignore

from .networks import get_networks
from .router import estimate_transfer_costs, select_cheapest_network
from .tx_sender import TransactionSender


app = FastAPI(title="L2 Gas‑Optimized Router", version="1.0.0")

# Determine the directory containing this file to serve static assets
MODULE_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(MODULE_DIR, "static")

# Mount static files under /static for dashboard assets
app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static",
)


class EstimateRequest(BaseModel):
    """Schema for estimation and routing requests."""

    from_address: str = Field(..., description="Hex‑encoded sender address")
    to_address: str = Field(..., description="Hex‑encoded recipient address")
    amount_eth: float = Field(..., gt=0, description="Amount of Ether to send, denominated in ETH")
    include_usd: bool = Field(True, description="Include estimated USD fees")


class RouteResponse(BaseModel):
    """Response model for route selection."""

    chosen_network: Optional[str]
    costs: Dict[str, Dict]


class SendRequest(BaseModel):
    """Schema for sending a transaction on a chosen network."""

    network: str = Field(..., description="Target network name (e.g. 'arbitrum')")
    from_address: str = Field(..., description="Hex‑encoded sender address")
    to_address: str = Field(..., description="Hex‑encoded recipient address")
    amount_eth: float = Field(..., gt=0, description="Amount of Ether to send, denominated in ETH")


@app.get("/networks")
def list_networks() -> Dict[str, Dict[str, str]]:
    """Return the configured Layer‑2 networks and their RPC endpoints."""
    networks = get_networks()
    return {
        name: {
            "rpc_url": cfg.rpc_url,
            "chain_id": cfg.chain_id,
            "native_symbol": cfg.native_symbol,
        }
        for name, cfg in networks.items()
    }


@app.get("/")
def get_root() -> FileResponse:
    """Serve the root HTML page for the dashboard."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    return FileResponse(index_path)


@app.post("/estimate")
async def estimate(request: EstimateRequest) -> Dict[str, Dict]:
    """Estimate transfer costs across all networks."""
    amount_wei = Web3.to_wei(request.amount_eth, "ether")
    costs = await estimate_transfer_costs(
        request.from_address,
        request.to_address,
        amount_wei,
        include_usd=request.include_usd,
    )
    return costs


@app.post("/route")
async def route(request: EstimateRequest) -> RouteResponse:
    """Select the cheapest network for the given transfer."""
    amount_wei = Web3.to_wei(request.amount_eth, "ether")
    costs = await estimate_transfer_costs(
        request.from_address,
        request.to_address,
        amount_wei,
        include_usd=request.include_usd,
    )
    chosen = select_cheapest_network(costs)
    return RouteResponse(chosen_network=chosen, costs=costs)


@app.post("/send")
async def send(request: SendRequest) -> Dict[str, str]:
    """Send a transaction on a specific network."""
    amount_wei = Web3.to_wei(request.amount_eth, "ether")
    sender = TransactionSender()
    try:
        tx_hash = sender.send_transfer(
            request.network,
            request.from_address,
            request.to_address,
            amount_wei,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"tx_hash": tx_hash}


@app.post("/route-and-send")
async def route_and_send(request: EstimateRequest) -> Dict[str, str | Dict]:
    """Automatically select the cheapest network and send a transaction."""
    amount_wei = Web3.to_wei(request.amount_eth, "ether")
    costs = await estimate_transfer_costs(
        request.from_address,
        request.to_address,
        amount_wei,
        include_usd=request.include_usd,
    )
    network = select_cheapest_network(costs)
    if network is None:
        raise HTTPException(status_code=500, detail="Failed to estimate costs on all networks")
    sender = TransactionSender()
    try:
        tx_hash = sender.send_transfer(
            network,
            request.from_address,
            request.to_address,
            amount_wei,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"network": network, "tx_hash": tx_hash, "costs": costs}
