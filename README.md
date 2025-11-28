# L2 Router Bot

**L2 Router Bot** is a self‑hosted service that automatically compares gas
fees across multiple Ethereum Layer‑2 networks and routes your
Ether transactions to the cheapest or fastest chain.  It exposes a
REST API built with FastAPI and includes an optional lightweight
dashboard for ad‑hoc usage.

## 🚀 Features

* **Multi‑network support** – currently supports Arbitrum One,
  Optimism and Base.  RPC endpoints can be overridden using
  environment variables.  Additional networks can be added easily.
* **Fee estimation** – calculates gas price, estimated gas usage and
  total fees in native token units.  Optionally fetches USD
  conversions via the CoinGecko API.
* **Route selection** – selects the cheapest network based on total
  estimated fees.  Networks where estimation fails are ignored.
* **Transaction broadcasting** – signs and broadcasts Ether
  transfers using a private key supplied via environment variables.
* **FastAPI backend** – provides `/networks`, `/estimate`, `/route`,
  `/send` and `/route-and-send` endpoints with JSON responses.
* **Optional dashboard** – static HTML/JS page served at the root
  path, allowing quick estimation and routing via a form.

## 👋 Project Structure

```
l2-router-bot/
│── main.py             # FastAPI application
│── networks.py         # Network configurations and Web3 client helpers
│── router.py           # Gas comparison and route selection logic
│── tx_sender.py        # Transaction signing and broadcasting helper
│── utils/
│     └── price_feed.py # Asynchronous price feed using CoinGecko
│── static/
│     └── index.html    # Minimal dashboard UI
│── tests/
│     └── test_router.py# Unit tests for route selection
│── .env                # Populate with PRIVATE_KEY and RPC overrides (not checked in)
│── requirements.txt    # Python dependencies
└── README.md           # This documentation
```

## 🔒 Security Considerations

Sending Ethereum transactions is an irreversible operation.  This
project **never** stores or exposes your private key in logs or
responses.  The private key must be supplied via the `PRIVATE_KEY`
environment variable (or passed explicitly to `TransactionSender`).

Before broadcasting a transaction, ensure that:

1. You trust the RPC endpoints you are connecting to.
2. You understand the fee structure on your selected network.
3. The `from_address` has sufficient funds to cover both the
   transfer amount and the gas fee.

Use the `/route` endpoint to inspect estimated costs before using
`/send` or `/route-and-send`.

## 💪 Usage

### 1. Clone the repository

```sh
git clone <this‑repo>
cd l2-router-bot
```

### 2. Create and activate a virtual environment (optional but recommended)

```sh
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```sh
pip install -r requirements.txt
```

### 4. Configure environment

Create a `.env` file in the project root containing your private
key and any RPC overrides.  For example:

```ini
PRIVATE_KEY=0xdeadbeef...
ARBITRUM_RPC_URL=https://arb1.arbitrum.io/rpc
OPTIMISM_RPC_URL=https://mainnet.optimism.io
BASE_RPC_URL=https://mainnet.base.org
```

**Never** commit your private key to version control.  In
production you may prefer to provide these variables via a secret
manager.

### 5. Run the application

Start the FastAPI app with Uvicorn:

```sh
uvicorn l2_router_bot.main:app --host 0.0.0.0 --port 8000 --reload
```

Navigate to `http://localhost:8000/` to view the dashboard, or use
the built‑in interactive API docs at `http://localhost:8000/docs`.

## 🌐 API Endpoints

### `GET /networks`

Returns a mapping of supported networks to their RPC endpoints,
chain IDs and native symbols.

### `POST /estimate`

Estimate transfer costs across all networks.

**Request body** (`application/json`):

```json
{
  "from_address": "0x...",
  "to_address": "0x...",
  "amount_eth": 0.01,
  "include_usd": true
}
```

**Response:** Per‑network gas price, estimated gas usage and fee
details.  Networks where estimation failed include an `error` key.

### `POST /route`

Select the cheapest network for the given transfer.

Returns the chosen network and the full set of cost estimates.

### `POST /send`

Send a transaction on a specific network.  Requires a loaded
private key.  Use only after inspecting the `/route` endpoint.

**Request body**:

```json
{
  "network": "optimism",
  "from_address": "0x...",
  "to_address": "0x...",
  "amount_eth": 0.01
}
```

### `POST /route-and-send`

Convenience endpoint: estimates costs, selects the cheapest network
and immediately broadcasts the transaction.  The response contains
the chosen network, the transaction hash and the full cost table.

## 🔮 Testing

Run the unit tests with:

```sh
pytest -q
```

The provided tests cover the route selection logic.  Integration
tests that talk to real RPC endpoints can be added by mocking Web3
clients or by running against a local testnet.

## 📊 Extending the Project

This project is intentionally modular.  You can extend it by:

* Adding support for more networks by populating
  `DEFAULT_NETWORKS` in `networks.py`.
* Implementing ERC‑20 token transfers in `tx_sender.py`.
* Caching price feed results to reduce API calls.
* Exposing additional strategies (e.g. prioritise speed over cost).
* Integrating authentication on the API.

Pull requests and issues are welcome!
