import streamlit as st
import pandas as pd
import json
import matplotlib.pyplot as plt
from pathlib import Path

# ===============================
# CONFIG
# ===============================

st.set_page_config(page_title="Monitor de ETFs", layout="wide")

# Caminho absoluto baseado no arquivo atual
ROOT_DIR = Path(__file__).parent.resolve()
DATA_DIR = ROOT_DIR / "data" / "etfs"
DASHBOARD_FILE = DATA_DIR / "dashboard_etfs.json"

# ===============================
# LOAD DATA
# ===============================

if not DASHBOARD_FILE.exists():
    st.error(f"Arquivo não encontrado: {DASHBOARD_FILE}")
    st.stop()

with open(DASHBOARD_FILE, "r", encoding="utf-8") as f:
    raw = json.load(f)

df_summary = pd.DataFrame(raw.get("summary", []))
df_signals = pd.DataFrame(raw.get("signals", []))

# ===============================
# HEADER
# ===============================

st.title("📊 Monitor de ETFs")
st.caption(
    f"Última atualização: {raw.get('updated_at')} | "
    f"IPCA 12m: {raw.get('ipca_12m')}%"
)

if df_summary.empty:
    st.warning("Dashboard carregado, mas sem dados de ETFs.")
    st.stop()

# ===============================
# TABELA — RESUMO
# ===============================

st.subheader("📌 Resumo dos ETFs")
st.dataframe(df_summary, use_container_width=True)

# ===============================
# TABELA — SINAIS
# ===============================

st.subheader("🚦 Sinais de Preço")

def color_signal(val):
    if val == "COMPRAR":
        return "background-color: #c6f6d5"
    if val == "REDUZIR":
        return "background-color: #fed7d7"
    return ""

if not df_signals.empty:
    st.dataframe(
        df_signals.style.applymap(color_signal, subset=["Sinal"]),
        use_container_width=True
    )
else:
    st.info("Nenhum sinal disponível.")

# ===============================
# GRÁFICO — PREÇO NORMALIZADO
# ===============================

st.subheader("📈 Comparação de Preço (Base 100)")

available_etfs = df_summary["ETF"].tolist()

selected = st.multiselect(
    "Selecione os ETFs",
    options=available_etfs,
    default=available_etfs
)

if selected:
    fig, ax = plt.subplots(figsize=(10, 5))

    for etf in selected:
        hist_file = DATA_DIR / f"{etf}_history.json"
        if not hist_file.exists():
            continue

        hist = pd.read_json(hist_file)
        ax.plot(hist["date"], hist["price_norm"], label=etf)

    ax.set_ylabel("Índice (Base 100)")
    ax.set_xlabel("Data")
    ax.legend()
    ax.grid(True)

    st.pyplot(fig)
else:
    st.info("Selecione pelo menos um ETF para visualizar o gráfico.")

# ===============================
# AJUDA
# ===============================

with st.expander("ℹ️ Como interpretar os sinais"):
    st.markdown("""
**🟢 COMPRAR**  
Preço bem abaixo da média móvel de 1 ano **e** distante do topo recente.

**🔴 REDUZIR**  
Preço muito acima da média **ou** próximo do topo do último ano.

**🟡 NEUTRO**  
Sem desvios relevantes.
""")
