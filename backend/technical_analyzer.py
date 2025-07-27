import os
import time
import warnings
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv

warnings.filterwarnings("ignore")


class TechnicalAnalyzer:
    """
    Fetches and cleans historical OHLCV data with Marketstack.

    Notes
    -----
    • Marketstack free tier allows 1,000 requests/month and 5 requests/second.
    • Both end-of-day and intraday data are supported.
    • Only stock symbols are supported here.
    """

    BASE_URL = "https://api.marketstack.com/v1"
    _MARKETSTACK_INTERVAL_MAP = {
        # intraday intervals (Basic Plan and higher)
        "1min": "1min",
        "5min": "5min", 
        "15min": "15min",
        "30min": "30min",
        "60min": "1hour",
        # daily data
        "1D": "daily",
        "1W": "weekly", 
        "1M": "monthly",
    }

    def __init__(self, api_key: Optional[str] = None, request_pause: float = 0.2):
        """
        Parameters
        ----------
        api_key : str, optional
            Marketstack API key. Loaded from environment if omitted.
        request_pause : float
            Seconds to wait between Marketstack calls (rate-limit helper).
            Free tier → 5 requests/second ⇒ 0.2s pause.
        """
        if api_key is None:
            load_dotenv()
            api_key = os.getenv("MARKETSTACK_API_KEY")

        if not api_key:
            raise ValueError(
                "MARKETSTACK_API_KEY not found. Add it to your .env or pass explicitly."
            )

        self.api_key = api_key
        self.request_pause = max(request_pause, 0)

    # PUBLIC METHODS
    def get_historical_data(
        self,
        symbols: List[str],
        interval: str = "1D",
        limit: int = 100,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Fetch and clean OHLCV data for multiple symbols.

        Parameters
        ----------
        symbols : list[str]
            Stock tickers (eg. ["AAPL", "MSFT"]).
        interval : str
            • Intraday: 1min,5min,15min,30min,60min (Basic Plan+)
            • Daily/Weekly/Monthly: 1D,1W,1M
        limit : int
            Number of data points to retrieve (max 1000).
        date_from : str, optional
            Start date in YYYY-MM-DD format.
        date_to : str, optional
            End date in YYYY-MM-DD format.

        Returns
        -------
        pd.DataFrame
            Cleaned data with columns:
            symbol, datetime, open, high, low, close, volume,
            price_change, price_change_pct, typical_price, true_range
        """
        print(f"Fetching Marketstack data for {len(symbols)} symbols …")
        dfs = []
        for idx, sym in enumerate(symbols, 1):
            try:
                raw = self._fetch_symbol(sym, interval, limit, date_from, date_to)
                if raw.empty:
                    print(f"No data for {sym}")
                    continue
                raw["symbol"] = sym
                dfs.append(raw)
                print(f"{sym}: {len(raw)} rows")
            except Exception as exc:
                print(f"{sym}: {exc}")

            # polite pause between calls
            if idx < len(symbols):
                time.sleep(self.request_pause)

        if not dfs:
            print("No historical data retrieved")
            return pd.DataFrame()

        combined = pd.concat(dfs, ignore_index=True)
        return self._clean_historical_data(combined)

    def get_latest_prices(self, symbols: List[str]) -> pd.DataFrame:
        """
        Convenience helper - returns most recent bar (per symbol).
        """
        latest = self.get_historical_data(symbols, interval="1D", limit=1)
        if latest.empty:
            return pd.DataFrame()

        return latest[["symbol", "datetime", "close", "volume", "price_change_pct"]]

    def validate_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Basic sanity checks.
        """
        if df.empty:
            return {"status": "empty", "issues": ["No data"]}

        issues, warns = [], []
        nulls = df.isna().sum()
        if nulls.any():
            issues.append(f"Missing: {nulls[nulls > 0].to_dict()}")

        dups = df.groupby(["symbol", "datetime"]).size()
        if (dups > 1).any():
            issues.append("Duplicate timestamps")

        big = df[np.abs(df["price_change_pct"]) > 50]
        if not big.empty:
            warns.append(f"{len(big)} extreme moves")

        counts = df["symbol"].value_counts()
        if counts.max() - counts.min() > counts.max() * 0.1:
            warns.append("Uneven record counts across symbols")

        return {
            "status": "valid" if not issues else "invalid",
            "records": len(df),
            "symbols": counts.size,
            "issues": issues,
            "warnings": warns,
        }

    # INTERNAL HELPERS
    def _fetch_symbol(
        self, 
        symbol: str, 
        interval: str, 
        limit: int,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> pd.DataFrame:
        """Call Marketstack and parse JSON into DataFrame."""
        
        # Determine endpoint based on interval
        if interval in ["1min", "5min", "15min", "30min", "60min"]:
            endpoint = "intraday"
            ms_interval = self._MARKETSTACK_INTERVAL_MAP[interval]
        else:
            endpoint = "eod"
            ms_interval = None

        url = f"{self.BASE_URL}/{endpoint}"
        
        params = {
            "access_key": self.api_key,
            "symbols": symbol,
            "limit": limit,
        }
        
        if ms_interval:
            params["interval"] = ms_interval
            
        if date_from:
            params["date_from"] = date_from
            
        if date_to:
            params["date_to"] = date_to

        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # Handle API errors
        if "error" in data:
            error_info = data["error"]
            error_msg = error_info.get("message", "Unknown error")
            error_code = error_info.get("code", "unknown")
            
            if error_code == "rate_limit_reached":
                print(f"⚠️ Marketstack Rate Limit: {error_msg}")
                raise ValueError(f"Rate limit reached: {error_msg}")
            elif error_code == "function_access_restricted":
                print(f"⚠️ Marketstack Access Restricted: {error_msg}")
                raise ValueError(f"Feature not available on current plan: {error_msg}")
            else:
                print(f"❌ Marketstack Error [{error_code}]: {error_msg}")
                raise ValueError(f"Marketstack API error: {error_msg}")

        # Check if we have data
        if "data" not in data or not data["data"]:
            print(f"❌ No data found for {symbol}")
            return pd.DataFrame()

        # Parse the data
        records = []
        for item in data["data"]:
            records.append({
                "datetime": pd.to_datetime(item["date"]),
                "open": float(item["open"]),
                "high": float(item["high"]), 
                "low": float(item["low"]),
                "close": float(item["close"]),
                "volume": float(item.get("volume", 0)),
            })

        return pd.DataFrame(records)

    @staticmethod
    def _map_interval(interval: str):
        """Return marketstack interval for given interval string."""
        if interval not in TechnicalAnalyzer._MARKETSTACK_INTERVAL_MAP:
            raise ValueError(
                f"Unsupported interval '{interval}'. "
                "Use one of: 1min,5min,15min,30min,60min,1D,1W,1M"
            )
        return TechnicalAnalyzer._MARKETSTACK_INTERVAL_MAP[interval]

    # DATA CLEANING + FEATURE ENGINEERING  
    def _clean_historical_data(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df

        df = df.sort_values(["symbol", "datetime"]).reset_index(drop=True)

        # strip impossible rows
        df = df[
            (df["open"] > 0)
            & (df["high"] > 0)
            & (df["low"] > 0)
            & (df["close"] > 0)
            & (df["volume"] >= 0)
            & (df["high"] >= df["low"])
        ]

        df = self._add_basic_features(df)

        cols = [
            "symbol",
            "datetime", 
            "open",
            "high",
            "low",
            "close",
            "volume",
            "price_change",
            "price_change_pct",
            "typical_price",
            "true_range",
        ]
        print(
            f"✓ Cleaned {len(df)} rows across {df['symbol'].nunique()} symbols "
            f"({df['datetime'].min()} → {df['datetime'].max()})"
        )
        return df[cols]

    @staticmethod
    def _add_basic_features(df: pd.DataFrame) -> pd.DataFrame:
        df["price_change"] = df.groupby("symbol")["close"].diff().fillna(0)
        df["price_change_pct"] = (
            df.groupby("symbol")["close"].pct_change(fill_method=None).fillna(0) * 100
        )
        df["typical_price"] = (df["high"] + df["low"] + df["close"]) / 3

        df["prev_close"] = df.groupby("symbol")["close"].shift(1)
        df["true_range"] = np.maximum(
            df["high"] - df["low"],
            np.maximum(
                np.abs(df["high"] - df["prev_close"]),
                np.abs(df["low"] - df["prev_close"]),
            ),
        )
        df["true_range"] = df["true_range"].fillna(df["high"] - df["low"])
        df.drop(columns="prev_close", inplace=True)
        return df


def prepare_data_for_ta_lib(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    out: Dict[str, pd.DataFrame] = {}
    for sym in df["symbol"].unique():
        tmp = df[df["symbol"] == sym].copy()
        tmp.sort_values("datetime", inplace=True)
        tmp["date"] = tmp["datetime"].dt.date
        out[sym] = tmp.reset_index(drop=True)
    return out
