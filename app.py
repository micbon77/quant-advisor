import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from data_loader import load_data
from strategy import run_strategy
from backtester import run_backtest

st.set_page_config(page_title="Sistema di Consulenza Investimenti", layout="wide")

def check_password():
    """Ritorna `True` se la password è corretta."""
    def password_entered():
        if st.session_state["password"] == st.secrets.get("password", "quantadmin123"):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Rimuove la password dalla memoria
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Inserisci la password per accedere alla Dashboard:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Inserisci la password per accedere alla Dashboard:", type="password", on_change=password_entered, key="password")
        st.error("Password errata 😕")
        return False
    else:
        return True

if not check_password():
    st.stop()


st.title("Sistema Automatizzato di Consulenza per Investimenti e Backtesting")
st.markdown("Strategia Absolute Momentum e Segui-Tendenza")

st.info("**Disclaimer Legale:** Questa applicazione ha scopo puramente educativo e di ricerca personale. Non costituisce in alcun modo consulenza finanziaria e i risultati passati dei backtest non sono garanzia di rendimenti futuri.")

# --- Sidebar Inputs ---
st.sidebar.header("Asset da Analizzare")
tickers_input = st.sidebar.text_input("Inserisci i Ticker (separati da virgola)", value="SPY, QQQ, GLD, TLT, BITO")
tickers_list = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

st.sidebar.header("Parametri della Strategia")
initial_capital = st.sidebar.number_input("Capitale Iniziale ($)", min_value=1000, max_value=1000000, value=10000, step=1000)
transaction_fee = st.sidebar.number_input("Costo di Transazione ($)", min_value=0.0, max_value=50.0, value=2.0, step=0.5)
sma_period = st.sidebar.slider("Periodo SMA (Giorni)", min_value=50, max_value=300, value=200, step=10)
mom_period = st.sidebar.slider("Periodo Momentum (Giorni)", min_value=100, max_value=300, value=252, step=1)

# --- Data Loading ---
@st.cache_data
def fetch_and_cache_data(tickers):
    return load_data(tickers=tickers, years=10)

with st.spinner("Caricamento dati di mercato..."):
    data_dict = fetch_and_cache_data(tickers_list)

if not data_dict:
    st.error("Impossibile caricare i dati.")
    st.stop()

# --- Process Strategy and Backtest ---
results = {}
metrics_list = []
recommendations = []

for ticker, df in data_dict.items():
    if len(df) == 0:
        st.warning(f"Nessun dato disponibile per {ticker}")
        continue
        
    # Run strategy
    df_strat = run_strategy(df, sma_period=sma_period, mom_period=mom_period)
    
    # Run backtest
    df_backtest, metrics = run_backtest(df_strat, initial_capital=initial_capital, transaction_fee=transaction_fee)
    
    results[ticker] = df_backtest
    
    if metrics:
        metrics['Asset'] = ticker
        metrics_list.append(metrics)
        
    # Get latest recommendation
    if len(df_strat) > 0:
        latest_date = df_strat.index[-1]
        latest_close = df_strat['Close'].iloc[-1]
        latest_signal = df_strat['Signal'].iloc[-1]
        actionable_signal = df_strat['Signal_Daily'].iloc[-1]
        
        # Determine display recommendation
        prev_signal = df_strat['Signal'].iloc[-2] if len(df_strat) > 1 else "CASH"
        
        if latest_signal == "BUY":
            rec = "MANTIENI (Posizione Lunga)" if prev_signal == "BUY" else "COMPRA"
        else:
            rec = "LIQUIDITÀ (Cash)"
            
        recommendations.append({
            "Asset": ticker,
            "Data": latest_date.strftime("%Y-%m-%d"),
            "Ultima Chiusura": f"${latest_close:.2f}",
            "Segnale Giornaliero": actionable_signal,
            "Posizione Corrente": latest_signal,
            "Raccomandazione": rec
        })

# --- Dashboard Layout ---

st.header("Raccomandazioni Giornaliere")
st.dataframe(pd.DataFrame(recommendations), width='stretch')

st.header("Metriche del Backtest")
if metrics_list:
    metrics_df = pd.DataFrame(metrics_list)
    cols = ['Asset'] + [c for c in metrics_df.columns if c != 'Asset']
    st.dataframe(metrics_df[cols].style.format({
        "Rendimento Totale (%)": "{:.2f}%",
        "Drawdown Massimo (%)": "{:.2f}%",
        "Indice di Sharpe": "{:.2f}",
        "Tasso di Vittoria (%)": "{:.2f}%",
        "Trade Totali": "{:d}"
    }), width='stretch')

st.header("Curve Azionarie (Equity)")
selected_asset = st.selectbox("Seleziona Asset da Visualizzare", options=list(results.keys()))

if selected_asset and selected_asset in results:
    df_plot = results[selected_asset]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['Strategy_Equity'], mode='lines', name='Equity della Strategia', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['BnH_Equity'], mode='lines', name='Equity Buy & Hold', line=dict(color='orange')))
    
    fig.update_layout(
        title=f"Curva Equity: Strategia vs Benchmark per {selected_asset}",
        xaxis_title="Data",
        yaxis_title="Valore del Portafoglio ($)",
        template="plotly_white",
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    with st.expander(f"Dati Recenti per {selected_asset}"):
        cols_to_show = ['Close', 'SMA', 'Momentum', 'Signal_Daily', 'Signal', 'Actual_Position', 'Strategy_Equity']
        cols_to_show = [c for c in cols_to_show if c in df_plot.columns]
        st.dataframe(df_plot[cols_to_show].tail(10))
