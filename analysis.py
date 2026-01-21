import yfinance as yf
import pandas as pd
import numpy as np
import json
import os
from bcb import sgs
from config import *

ETFS = {
    "BOVA11.SA": {
        "name": "BOVA11",
        "taxa_etf": 0.0010  # 0,10% a.a.
    },
    "IVVB11.SA": {
        "name": "IVVB11",
        "taxa_etf": 0.0023  # 0,23% a.a.
    },
    "GOLD11.SA": {
        "name": "GOLD11",
        "taxa_etf": 0.0030  # 0,30% a.a.
    },
    "BIXN39.SA": {
        "name": "BIXN39",
        "taxa_etf": 0.0030  # ~0,30% a.a. (BDR ETF)
    }
}

# Custos
TAXA_B3 = 0.0003  # 0,03% a.a.

# Médias móveis
MM_CURTA = 50
MM_LONGA = 200

# Alertas
DRAWDOWN_ALERT = -0.20
DIST_MM200_ALERT = -0.05

# ----------------------------------
# PARÂMETROS DE TEMPO
# ----------------------------------
DAYS_1Y = 252
DAYS_5Y = 252 * 5

os.makedirs("data", exist_ok=True)

# ----------------------------------
# INFLAÇÃO (BACEN - SGS)
# ----------------------------------

import yfinance as yf
import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime
from bcb import sgs

# =====================
# Config
# =====================
ETFS = {
    "BOVA11": "BOVA11.SA",
    "IVVB11": "IVVB11.SA",
    "GOLD11": "GOLD11.SA",
    "BIXN39": "BIXN39.SA"
}

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# =====================
# IPCA 12m
# =====================
def get_ipca_12m():
    df = sgs.get({"ipca": 433})
    return df["ipca"].iloc[-1] / 100

IPCA_12M = get_ipca_12m()

# =====================
# Helpers
# =====================
def annualized_return(prices):
    return (prices.iloc[-1] / prices.iloc[0]) ** (252 / len(prices)) - 1

def max_drawdown(prices):
    cummax = prices.cummax()
    return (prices / cummax - 1).min()

# =====================
# Loop principal
# =====================
summary = []
signals = []

for etf, ticker in ETFS.items():
    df = yf.download(ticker, period="6y", auto_adjust=True, progress=False)
    df = df.dropna()

    close = df["Close"]

    # Médias
    df["ma_1y"] = close.rolling(252).mean()

    price = close.iloc[-1]
    ma_1y = df["ma_1y"].iloc[-1]

    # Retornos
    ret_1a = price / close.iloc[-252] - 1
    ret_5a = annualized_return(close.tail(252 * 5))
    ret_real_1a = (1 + ret_1a) / (1 + IPCA_12M) - 1

    # Risco
    vol = close.pct_change().std() * np.sqrt(252)
    dd = max_drawdown(close)

    # Topo / fundo 1a
    max_1a = close.tail(252).max()
    min_1a = close.tail(252).min()

    dist_ma = price / ma_1y - 1
    dist_topo = price / max_1a - 1

    # Sinal
    if dist_ma < -0.10 and dist_topo < -0.20:
        signal = "COMPRAR"
    elif dist_ma > 0.20 or dist_topo > -0.05:
        signal = "REDUZIR"
    else:
        signal = "NEUTRO"

    # Histórico normalizado
    hist = (close / close.iloc[0] * 100).reset_index()
    hist.columns = ["date", "price_norm"]
    hist["date"] = hist["date"].astype(str)
    hist.to_json(DATA_DIR / f"{etf}_history.json", orient="records")

    # Summary
    summary.append({
        "ETF": etf,
        "Preço": round(price, 2),
        "Retorno 1a (%)": round(ret_1a * 100, 2),
        "Retorno real 1a (%)": round(ret_real_1a * 100, 2),
        "Retorno 5a a.a. (%)": round(ret_5a * 100, 2),
        "Volatilidade (%)": round(vol * 100, 2),
        "Drawdown máx (%)": round(dd * 100, 2)
    })

    signals.append({
        "ETF": etf,
        "Preço": round(price, 2),
        "Dist. MM 1a (%)": round(dist_ma * 100, 2),
        "Dist. topo 1a (%)": round(dist_topo * 100, 2),
        "Sinal": signal
    })

# =====================
# Salva JSONs
# =====================
output = {
    "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    "ipca_12m": round(IPCA_12M * 100, 2),
    "summary": summary,
    "signals": signals
}

with open(DATA_DIR / "dashboard.json", "w") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)
