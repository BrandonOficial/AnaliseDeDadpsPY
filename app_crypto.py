import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- Configuração da Página ---
st.set_page_config(layout="wide", page_title="Crypto Trader Pro", page_icon="📊")

# --- Funções de Dados ---
@st.cache_data(ttl=300)
def get_ohlc_data(coin_id: str, days: str) -> pd.DataFrame:
    """
    Busca dados OHLC (Open, High, Low, Close) na CoinGecko.
    """
    try:
        # Endpoint específico para velas (OHLC)
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc"
        params = {'vs_currency': 'usd', 'days': days}
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        if not data: return pd.DataFrame()
        
        # Formato CoinGecko OHLC: [time, open, high, low, close]
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close'])
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        return df
    except Exception as e:
        st.error(f"Erro na API: {e}")
        return pd.DataFrame()

def calculate_rsi(df: pd.DataFrame, period=14):
    """
    Calcula o RSI (Relative Strength Index) manualmente com Pandas.
    """
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

# --- Funções de Visualização ---
def plot_candlestick(df: pd.DataFrame, coin_name: str):
    """
    Cria o gráfico de velas (Candlestick) profissional.
    """
    fig = go.Figure()

    # Adiciona as Velas
    fig.add_trace(go.Candlestick(
        x=df['date'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='Preço'
    ))

    fig.update_layout(
        title=f"Análise Técnica: {coin_name}",
        yaxis_title='Preço (USD)',
        xaxis_rangeslider_visible=False, # Remove o slider inferior para limpar
        template="plotly_dark",
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)

def plot_rsi(df: pd.DataFrame):
    """
    Plota o indicador RSI separado.
    """
    fig = go.Figure()
    
    # Linha do RSI
    fig.add_trace(go.Scatter(x=df['date'], y=df['RSI'], name='RSI', line=dict(color='orange')))
    
    # Linhas de referência (70 = Sobrecomprado, 30 = Sobrevendido)
    fig.add_hrect(y0=70, y1=100, line_width=0, fillcolor="red", opacity=0.2)
    fig.add_hrect(y0=0, y1=30, line_width=0, fillcolor="green", opacity=0.2)
    
    fig.update_layout(
        title="Indicador RSI (14 dias)",
        yaxis_title="Força (0-100)",
        yaxis_range=[0, 100],
        template="plotly_dark",
        height=300
    )
    st.plotly_chart(fig, use_container_width=True)

# --- Main ---
def main():
    st.title("📊 Crypto Trader Pro")
    
    # Sidebar
    st.sidebar.header("Setup")
    coins = {"Bitcoin": "bitcoin", "Ethereum": "ethereum", "Solana": "solana", "Ripple": "ripple"}
    selected_coin = st.sidebar.selectbox("Ativo", list(coins.keys()))
    
    # CoinGecko OHLC aceita dias específicos: 1, 7, 14, 30, 90, 180, 365
    days = st.sidebar.select_slider("Janela de Tempo (Dias)", options=["7", "14", "30", "90", "180", "365"], value="30")
    
    coin_id = coins[selected_coin]

    # Processamento
    with st.spinner("Calculando indicadores..."):
        df = get_ohlc_data(coin_id, days)
        
        if not df.empty:
            # Calcular Indicadores Técnicos
            df = calculate_rsi(df)
            
            # Área Principal
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(f"Análise de {selected_coin}")
            with col2:
                # Botão de Download (Feature Nova!)
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Baixar Dados (CSV)",
                    data=csv,
                    file_name=f"{coin_id}_history.csv",
                    mime='text/csv',
                )

            # 1. Gráfico Principal (Candles)
            plot_candlestick(df, selected_coin)
            
            # 2. Gráfico Secundário (RSI)
            plot_rsi(df)

            # 3. Explicação do RSI para o usuário
            with st.expander("ℹ️ O que é o gráfico laranja (RSI)?"):
                st.markdown("""
                **RSI (Índice de Força Relativa):**
                * **Acima de 70 (Área Vermelha):** A moeda pode estar **cara demais** (Sobrecomprada). Chance de cair.
                * **Abaixo de 30 (Área Verde):** A moeda pode estar **barata demais** (Sobrevendida). Chance de subir.
                """)
            
            st.divider()
            st.subheader("Dados Detalhados")
            st.dataframe(df.sort_values('date', ascending=False), use_container_width=True)
            
        else:
            st.warning("Não foi possível carregar os dados OHLC.")

if __name__ == "__main__":
    main()