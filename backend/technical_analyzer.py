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
    Fetches and cleans historical OHLCV data with Alpha Vantage.

    Notes
    -----
    • Alpha Vantage free tier allows 5 requests/min and 500 requests/day.
      Automatic throttling (sleep) is included below.
    • Only stock symbols are supported here.
    """

    BASE_URL = "https://www.alphavantage.co/query"
    _AV_FUN_MAP = {
        # intraday intervals
        "1min": ("TIME_SERIES_INTRADAY", "1min"),
        "5min": ("TIME_SERIES_INTRADAY", "5min"),
        "15min": ("TIME_SERIES_INTRADAY", "15min"),
        "30min": ("TIME_SERIES_INTRADAY", "30min"),
        "60min": ("TIME_SERIES_INTRADAY", "60min"),
        # daily / weekly / monthly
        "1D": ("TIME_SERIES_DAILY", None),
        "1W": ("TIME_SERIES_WEEKLY", None),
        "1M": ("TIME_SERIES_MONTHLY", None),
    }

    def __init__(self, av_api_key: Optional[str] = None, request_pause: float = 12.0):
        """
        Parameters
        ----------
        av_api_key : str, optional
            Alpha Vantage API key.  Loaded from environment if omitted.
        request_pause : float
            Seconds to wait between Alpha Vantage calls (rate-limit helper).
            Free tier → 5 requests/min ⇒ 12 s pause.
        """
        if av_api_key is None:
            load_dotenv()
            av_api_key = os.getenv("ALPHAVANTAGE_API_KEY")

        if not av_api_key:
            raise ValueError(
                "ALPHAVANTAGE_API_KEY not found.  Add it to your .env or pass explicitly."
            )

        self.api_key = av_api_key
        self.request_pause = max(request_pause, 0)

    # PUBLIC METHODS
    def get_historical_data(
        self,
        symbols: List[str],
        interval: str = "60min",
        outputsize: str = "compact",
    ) -> pd.DataFrame:
        """
        Fetch and clean OHLCV data for multiple symbols.

        Parameters
        ----------
        symbols : list[str]
            Stock tickers (eg. ["AAPL", "MSFT"]).
        interval : str
            • Intraday: 1min,5min,15min,30min,60min  
            • Daily/Weekly/Monthly use "1D","1W","1M".
        outputsize : str
            'compact' (latest 100 pts) or 'full' (all available).
            Ignored for weekly/monthly.

        Returns
        -------
        pd.DataFrame
            Cleaned data with columns:
            symbol, datetime, open, high, low, close, volume,
            price_change, price_change_pct, typical_price, true_range
        """
        print(f"Fetching Alpha Vantage data for {len(symbols)} symbols …")
        dfs = []
        for idx, sym in enumerate(symbols, 1):
            try:
                raw = self._fetch_symbol(sym, interval, outputsize)
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
        latest = self.get_historical_data(symbols, interval="1D", outputsize="compact")
        if latest.empty:
            return pd.DataFrame()

        return (
            latest.sort_values("datetime")
            .groupby("symbol")
            .tail(1)
            .reset_index(drop=True)[
                ["symbol", "datetime", "close", "volume", "price_change_pct"]
            ]
        )

    def validate_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        basic sanity checks.
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
        self, symbol: str, interval: str, outputsize: str
    ) -> pd.DataFrame:
        """Call Alpha Vantage and parse JSON into DataFrame."""
        func, av_interval = self._map_interval(interval)

        params = {
            "function": func,
            "symbol": symbol,
            "apikey": self.api_key,
            "datatype": "json",
        }
        if func == "TIME_SERIES_INTRADAY":
            params["interval"] = av_interval
            params["outputsize"] = outputsize  # compact/full

        resp = requests.get(self.BASE_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # Alpha Vantage nests data under a key that starts with "Time Series"
        key = next(
            (k for k in data.keys() if "Time Series" in k), None
        )
        if key is None:
            # API error message
            raise ValueError(data.get("Note") or data.get("Error Message") or "Unknown")

        records = []
        for dt_str, bar in data[key].items():
            records.append(
                {
                    "datetime": pd.to_datetime(dt_str),
                    "open": float(bar["1. open"]),
                    "high": float(bar["2. high"]),
                    "low": float(bar["3. low"]),
                    "close": float(bar["4. close"]),
                    "volume": float(bar.get("5. volume", 0)),
                }
            )

        return pd.DataFrame(records)

    @staticmethod
    def _map_interval(interval: str):
        """Return (function, av_interval) tuple for given interval string."""
        if interval not in TechnicalAnalyzer._AV_FUN_MAP:
            raise ValueError(
                f"Unsupported interval '{interval}'. "
                "Use one of: 1min,5min,15min,30min,60min,1D,1W,1M"
            )
        return TechnicalAnalyzer._AV_FUN_MAP[interval]

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
