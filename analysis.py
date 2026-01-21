import yfinance as yf
import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime
from bcb import sgs

# =====================
# Configurações
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
# IPCA 12 meses (BCB)
# =====================
def get_ipca_12m():
    df = sgs.get({"ipca": 433})
    return df["ipca"].iloc[-1] / 100

IPCA_12M = get_ipca_12m()

# =====================
# Funções auxiliares
# =====================
def annualized_return(prices):
    return (prices.iloc[-1] / prices.iloc[0]) ** (252 / len(prices)) - 1

def max_drawdown(prices):
    cummax = prices.cummax()
    return (prices / cummax - 1).min()

# =====================
# Processamento
# =====================
summary = []
signals = []

for etf, ticker in ETFS.items():
    df = yf.download(
        ticker,
        period="6y",
        auto_adjust=True,
        progr
