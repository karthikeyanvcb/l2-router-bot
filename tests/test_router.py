"""Unit tests for router selection logic.

The tests in this file verify that the cheapest network is selected
correctly when provided with synthetic cost data.  Network
estimation is not exercised here because it requires access to live
RPC endpoints.  For integration testing you may provide mocked
Web3 clients or run tests against a local blockchain instance.
"""

from l2_router_bot.router import select_cheapest_network


def test_select_cheapest_network_simple():
    costs = {
        "arbitrum": {"total_fee_wei": 100},
        "optimism": {"total_fee_wei": 50},
        "base": {"total_fee_wei": 75},
    }
    assert select_cheapest_network(costs) == "optimism"


def test_select_cheapest_network_ignores_errors():
    costs = {
        "arbitrum": {"error": "RPC unavailable"},
        "optimism": {"total_fee_wei": 90},
        "base": {"total_fee_wei": 120},
    }
    assert select_cheapest_network(costs) == "optimism"


def test_select_cheapest_network_none_when_all_fail():
    costs = {
        "arbitrum": {"error": "failed"},
        "optimism": {"error": "failed"},
    }
    assert select_cheapest_network(costs) is None
