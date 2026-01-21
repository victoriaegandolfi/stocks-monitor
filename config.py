# config.py

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
