"""Polymarket API client with rate limiting and retries."""

import time
from typing import Any, Dict, Optional

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.core.observability import log_duration, logger, metrics


class PolymarketClient:
    """
    Polymarket API client wrapper.

    NOTE: This implementation assumes Polymarket uses a GraphQL API.
    If the actual API is REST-based, adjust the request format accordingly.
    """

    BASE_URL = "https://clob.polymarket.com"  # ASSUMPTION: Base URL
    GRAPHQL_URL = f"{BASE_URL}/graphql"  # ASSUMPTION: GraphQL endpoint

    def __init__(
        self,
        api_key: Optional[str] = None,
        rate_limit_per_second: float = 10.0,
        timeout: int = 30,
    ):
        """
        Initialize client.

        Args:
            api_key: API key if required (ASSUMPTION: may not be needed for public data)
            rate_limit_per_second: Max requests per second
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.rate_limit_per_second = rate_limit_per_second
        self.timeout = timeout
        self._last_request_time = 0.0
        self._min_request_interval = 1.0 / rate_limit_per_second

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        self.client = httpx.Client(
            headers=headers,
            timeout=timeout,
            follow_redirects=True,
        )

    def _enforce_rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            sleep_time = self._min_request_interval - elapsed
            time.sleep(sleep_time)
        self._last_request_time = time.time()

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def _request(
        self,
        method: str,
        url: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request with retries and rate limiting."""
        self._enforce_rate_limit()

        with log_duration("api.request", method=method, url=url):
            try:
                response = self.client.request(method=method, url=url, json=json, params=params)
                response.raise_for_status()
                metrics.increment("api.requests.success", tags={"method": method})
                return response.json()
            except httpx.HTTPStatusError as e:
                metrics.increment("api.requests.error", tags={"status": str(e.response.status_code)})
                logger.error(
                    "api.request.error",
                    status_code=e.response.status_code,
                    response_text=e.response.text[:500],
                )
                raise
            except Exception as e:
                metrics.increment("api.requests.error", tags={"error_type": type(e).__name__})
                raise

    def query_graphql(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute GraphQL query.

        ASSUMPTION: Polymarket uses GraphQL. Adjust if REST-based.
        """
        payload = {"query": query, "variables": variables or {}}
        return self._request("POST", self.GRAPHQL_URL, json=payload)

    def get_markets(
        self,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        active: bool = True,
    ) -> Dict[str, Any]:
        """
        Fetch markets.

        ASSUMPTION: GraphQL query structure. Adjust based on actual Polymarket API.
        """
        query = """
        query GetMarkets($limit: Int, $cursor: String, $active: Boolean) {
            markets(limit: $limit, cursor: $cursor, active: $active) {
                data {
                    id
                    question
                    description
                    endDate
                    resolutionSource
                    category
                    tags
                    liquidity
                    volume24h
                    createdAt
                    updatedAt
                    outcomes {
                        id
                        name
                        tokenAddress
                    }
                }
                nextCursor
            }
        }
        """
        variables = {"limit": limit, "cursor": cursor, "active": active}
        result = self.query_graphql(query, variables)
        # ASSUMPTION: Response structure. Adjust based on actual API.
        return result.get("data", {}).get("markets", {})

    def get_trades(
        self,
        market_id: Optional[str] = None,
        since: Optional[str] = None,  # ISO timestamp string
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fetch trades.

        ASSUMPTION: GraphQL query structure. Adjust based on actual Polymarket API.
        """
        query = """
        query GetTrades($marketId: String, $since: String, $limit: Int, $cursor: String) {
            trades(marketId: $marketId, since: $since, limit: $limit, cursor: $cursor) {
                data {
                    id
                    marketId
                    outcomeId
                    price
                    quantity
                    timestamp
                    side
                    takerAddress
                    makerAddress
                    transactionHash
                }
                nextCursor
            }
        }
        """
        variables = {
            "marketId": market_id,
            "since": since,
            "limit": limit,
            "cursor": cursor,
        }
        result = self.query_graphql(query, variables)
        return result.get("data", {}).get("trades", {})

    def get_price_snapshots(
        self,
        market_id: Optional[str] = None,
        since: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fetch current price/probability snapshots.

        ASSUMPTION: GraphQL query structure. Adjust based on actual Polymarket API.
        """
        query = """
        query GetPriceSnapshots($marketId: String, $since: String) {
            priceSnapshots(marketId: $marketId, since: $since) {
                data {
                    marketId
                    outcomeId
                    timestamp
                    impliedProbability
                    bid
                    ask
                    mid
                    spread
                    volume24h
                    liquidity
                }
            }
        }
        """
        variables = {"marketId": market_id, "since": since}
        result = self.query_graphql(query, variables)
        return result.get("data", {}).get("priceSnapshots", {})

    def close(self):
        """Close HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

