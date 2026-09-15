# =============================================================================
# MODULE 01 — PROJECT SETUP
# =============================================================================

import logging
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt


REGIME_TICKER = "QQQ"
TRADE_TICKER = "TQQQ"

INTERVAL = "1h"
PERIOD = "60d"
MARKET_TZ = "America/New_York"

DATA_DIR = Path("data")
CACHE_DIR = DATA_DIR / "cache"

CACHE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
)


plt.rcParams["figure.figsize"] = (15, 6)
plt.rcParams["axes.titlesize"] = 14
plt.rcParams["axes.titleweight"] = "bold"
plt.rcParams["lines.linewidth"] = 1.5


print(
    f"Environment ready | "
    f"Regime: {REGIME_TICKER} | "
    f"Trade: {TRADE_TICKER}"
)
