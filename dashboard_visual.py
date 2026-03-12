import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# --- 1. SEITEN-KONFIGURATION ---
st.set_page_config(page_title="Quant Stock Command Center", layout="wide")
st.title("🛡️ Accumulation & Risk Dashboard")
st.markdown("---")

# --- 2. WECHSELKURSE & MAKRO ---
@st.cache_data(ttl=300)
def hole_finanz_daten():
    # S&P 500 für Makro-Trend
    spy = yf.Ticker("SPY")
    hist_spy = spy.history(period="1y")
    spy_sma200 = hist_spy['Close'].rolling(window=200).mean().iloc[-1]
    spy_aktuell = hist_spy['Close'].iloc[-1]
    
    # Live Wechselkurse
    usd_eur_rate = yf.Ticker("EURUSD=X").history(period="1d")['Close'].iloc[-1]
    hkd_eur_rate = yf.Ticker("EURHKD=X").history(period="1d")['Close'].iloc[-1]
    
    return spy_aktuell, spy_sma200, usd_eur_rate, hkd_eur_rate

try:
    spy_preis, spy_sma200, eur_usd_rate, eur_hkd_rate = hole_finanz_daten()
    spy_abstand = ((spy_preis - spy_sma200) / spy_sma200) * 100
    
    # --- MAKRO ÜBERBLICK OBEN ---
    st.subheader("🌍 Markt & Makro Übersicht")
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    
    m_col1.metric("SPY (S&P 500)", f"${spy_preis:.2f}")
    m_col2.metric("SMA 200 Abstand", f"{spy_abstand:.2f}%", 
                  delta="BULLISH" if spy_abstand > 0 else "BEARISH")
    m_col3.metric("EUR/USD Rate", f"${eur_usd_rate:.4f}")
    m_col4.metric("EUR/HKD Rate", f"{eur_hkd_rate:.4f} HK$")
    
except Exception as e:
    st.error(f"Fehler beim Laden der Makro-Daten: {e}")

st.markdown("---")

# --- 3. DEIN PORTFOLIO ---
# Inklusive deines neuen MSCI World ETFs (EUNL.DE)
portfolio = {
    "PYPL": {"kaufpreis_eur": 57.76, "anzahl": 4.345558},
    "2FE.DE": {"kaufpreis_eur": 361.64, "anzahl": 0.694637},
    "1211.HK": {"kaufpreis_eur": 11.5, "anzahl": 26.262574},
    "EUNL.DE": {"kaufpreis_eur": 108.15, "anzahl": 2.322125},
}

tabelle_daten = []

for ticker, daten in portfolio.items():
    aktie = yf.Ticker(ticker)
    hist = aktie.history(period="6mo")
    if not hist.empty:
        preis_lokal = hist['Close'].iloc[-1]
        
        # Währungs-Check & Umrechnung
        if ticker.endswith(".DE") or ticker.endswith(".F"): 
            rate = 1.0
        elif ticker.endswith(".HK"): 
            rate = eur_hkd_rate
        else: 
            rate = eur_usd_rate
            
        preis_eur = preis_lokal / rate
        wert_eur = preis_eur * daten["anzahl"]
        investiert_eur = daten["kaufpreis_eur"] * daten["anzahl"]
        pnl_prozent = ((preis_eur - daten["kaufpreis_eur"]) / daten["kaufpreis_eur"]) * 100
        
        tabelle_daten.append({
            "Ticker": ticker,
            "Price": preis_eur,
            "Avg": daten["kaufpreis_eur"],
            "P&L%": pnl_prozent,
            "Shares": daten["anzahl"],
            "Value": wert_eur
        })

df = pd.DataFrame(tabelle_daten)

# --- 4. VISUALISIERUNG ---
col_table, col_pie = st.columns([2, 1])
with col_table:
    st.subheader("💼 Portfolio Status")
    st.dataframe(df.style.format(precision=2), use_container_width=True, hide_index=True)

with col_pie:
    fig_pie = px.pie(df, values='Value', names='Ticker', hole=0.4, title="Gewichtung")
    st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("---")

# --- 5. DIE ACCUMULATION LADDER ---
st.subheader("🪜 Accumulation Ladders (Nachkauf-Strategie)")
st.info("Nutze diese Level, um mathematisch sinnvoll nachzukaufen, wenn die Aktie weiter fällt.")

minus_stocks = df[df['P&L%'] < 0]

if not minus_stocks.empty:
    cols = st.columns(len(minus_stocks))
    for i, row in enumerate(minus_stocks.itertuples()):
        with cols[i]:
            st.markdown(f"### {row.Ticker}")
            stufen = [0.90, 0.80, 0.70] # -10%, -20%, -30% vom aktuellen Preis
            
            for s in stufen:
                target_price = row.Price * s
                abstand_zu_einstieg = ((target_price - row.Avg) / row.Avg) * 100
                
                st.write(f"**Stufe {int((1-s)*100)}% Drop:**")
                st.code(f"Kauf bei €{target_price:.2f}\n({abstand_zu_einstieg:.1f}% vs. Avg)")
else:
    st.success("Aktuell keine Positionen im Minus. Monk Mode: Abwarten.")

# Performance Balken am Ende
st.markdown("---")
fig_bar = px.bar(df, x='Ticker', y='P&L%', color='P&L%', title="Relative Performance der Positionen",
                  color_continuous_scale='RdYlGn', range_color=[-20, 20])

st.plotly_chart(fig_bar, use_container_width=True)

