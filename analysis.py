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
    return float(df["ipca"].iloc[-1]) / 100

IPCA_12M = get_ipca_12m()

# =====================
# Funções auxiliares
# =====================
def annualized_return(prices: pd.Series) -> float:
    prices = prices.dropna()
    return (prices.iloc[-1] / prices.iloc[0]) ** (252 / len(prices)) - 1

def max_drawdown(prices: pd.Series) -> float:
    prices = prices.dropna()
    cummax = prices.cummax()
    return float((prices / cummax - 1).min())

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
        progress=False
    )

    if df.empty or "Close" not in df:
        continue

    close = df["Close"].dropna()

    if len(close) < 50:
        continue

    price = close.iloc[-1].item()

    # =====================
    # Média móvel 1 ano
    # =====================
    ma_1y = close.rolling(252).mean().iloc[-1]
    ma_1y = ma_1y.item() if not np.isnan(ma_1y) else np.nan

    # =====================
    # Retornos
    # =====================
    ret_1a = (
        (price / close.iloc[-252].item() - 1)
        if len(close) >= 252 else np.nan
    )

    ret_5a = (
        annualized_return(close.tail(252 * 5))
        if len(close) >= 252 * 5 else np.nan
    )

    ret_real_1a = (
        (1 + ret_1a) / (1 + IPCA_12M) - 1
        if not np.isnan(ret_1a) else np.nan
    )

    # =====================
    # Risco
    # =====================
    vol = close.pct_change().std() * np.sqrt(252)
    dd = max_drawdown(close)

    # =====================
    # Topo 1 ano
    # =====================
    max_1a = (
        close.tail(252).max().item()
        if len(close) >= 252 else np.nan
    )

    # =====================
    # Sinal de preço
    # =====================
    dist_ma = np.nan
    dist_topo = np.nan
    signal = "NEUTRO"

    if not np.isnan(ma_1y) and not np.isnan(max_1a):
        dist_ma = price / ma_1y - 1
        dist_topo = price / max_1a - 1

        if dist_ma < -0.10 and dist_topo < -0.20:
            signal = "COMPRAR"
        elif dist_ma > 0.20 or dist_topo > -0.05:
            signal = "REDUZIR"

    # =====================
    # Histórico normalizado
    # =====================
    hist = (close / close.iloc[0] * 100).reset_index()
    hist.columns = ["date", "price_norm"]
    hist["date"] = hist["date"].astype(str)

    hist.to_json(
        DATA_DIR / f"{etf}_history.json",
        orient="records"
    )

    # =====================
    # Outputs
    # =====================
    summary.append({
        "ETF": etf,
        "Preço": round(price, 2),
        "Retorno 1a (%)": round(ret_1a * 100, 2) if not np.isnan(ret_1a) else None,
        "Retorno real 1a (%)": round(ret_real_1a * 100, 2) if not np.isnan(ret_real_1a) else None,
        "Retorno 5a a.a. (%)": round(ret_5a * 100, 2) if not np.isnan(ret_5a) else None,
        "Volatilidade (%)": round(vol * 100, 2),
        "Drawdown máx (%)": round(dd * 100, 2)
    })

    signals.append({
        "ETF": etf,
        "Preço": round(price, 2),
        "Dist. MM 1a (%)": round(dist_ma * 100, 2) if not np.isnan(dist_ma) else None,
        "Dist. topo 1a (%)": round(dist_topo * 100, 2) if not np.isnan(dist_topo) else None,
        "Sinal": signal
    })

# =====================
# Salva JSON principal
# =====================
output = {
    "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    "ipca_12m": round(IPCA_12M * 100, 2),
    "summary": summary,
    "signals": signals
}

with open(DATA_DIR / "dashboard.json", "w") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)
