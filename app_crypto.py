import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- Configuração Básica ---
st.set_page_config(layout="centered", page_title="Crypto Pro View")

# --- Função de Pegar Dados ---
@st.cache_data(ttl=300) 
def pegar_dados_completos(moeda_id, dias):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{moeda_id}/market_chart"
        params = {'vs_currency': 'usd', 'days': dias, 'interval': 'daily'}
        
        resposta = requests.get(url, params=params)
        dados = resposta.json()
        
        # 1. Preços
        df = pd.DataFrame(dados['prices'], columns=['timestamp', 'preco'])
        df['data'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # 2. Volumes
        df_vol = pd.DataFrame(dados['total_volumes'], columns=['timestamp', 'volume'])
        
        # Junta tudo
        df_final = pd.merge(df, df_vol, on='timestamp')
        
        # 3. Média Móvel
        df_final['media_movel'] = df_final['preco'].rolling(window=7).mean()
        
        return df_final
    except:
        return pd.DataFrame()

# --- Interface do Usuário ---
def main():
    st.title("🎯 Monitor de Cripto Simplificado")
    
    # --- CONFIGURAÇÕES (Sidebar) ---
    st.sidebar.header("Configurações")
    opcoes = {"Bitcoin": "bitcoin", "Ethereum": "ethereum", "Solana": "solana", "Ripple": "ripple"}
    nome_moeda = st.sidebar.selectbox("Moeda", list(opcoes.keys()))
    dias = st.sidebar.radio("Período", ["30", "90", "365"], index=0, horizontal=True)
    mostrar_media = st.sidebar.checkbox("Mostrar Média Móvel (7d)")
    
    id_moeda = opcoes[nome_moeda]
    
    # --- PROCESSAMENTO ---
    df = pegar_dados_completos(id_moeda, dias)
    
    if not df.empty:
        # Cálculos Preço
        preco_atual = df['preco'].iloc[-1]
        preco_inicio = df['preco'].iloc[0]
        variacao = ((preco_atual - preco_inicio) / preco_inicio) * 100
        preco_max = df['preco'].max()
        
        # Cálculos Volume (NOVIDADE AQUI)
        vol_medio = df['volume'].mean()
        vol_max = df['volume'].max()
        vol_min = df['volume'].min()
        
        # --- DASHBOARD DE MÉTRICAS ---
        st.markdown("### 💵 Métricas de Preço")
        col1, col2, col3 = st.columns(3)
        col1.metric("Preço Atual", f"$ {preco_atual:,.2f}")
        col2.metric("Variação", f"{variacao:.2f}%", delta_color="normal")
        col3.metric("Preço Máximo", f"$ {preco_max:,.2f}")
        
        st.markdown("### 📊 Métricas de Volume")
        col4, col5, col6 = st.columns(3)
        col4.metric("Volume Médio", f"$ {vol_medio:,.0f}")
        col5.metric("Maior Volume", f"$ {vol_max:,.0f}", delta="Pico", delta_color="off")
        col6.metric("Menor Volume", f"$ {vol_min:,.0f}", delta="Vale", delta_color="off")
        
        st.divider()

        # --- GRÁFICO PREÇO ---
        fig = px.area(
            df, x='data', y='preco',
            title=f"Evolução do Preço: {nome_moeda}",
            labels={'data': 'Data', 'preco': 'Preço (USD)'}
        )
        fig.update_traces(line_color='#8257E5')
        
        if mostrar_media:
            fig.add_trace(go.Scatter(
                x=df['data'], y=df['media_movel'],
                mode='lines', name='Média 7 Dias',
                line=dict(color='orange', width=2, dash='dot')
            ))

        fig.update_layout(yaxis_tickprefix="$", hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
        
        # --- GRÁFICO VOLUME ---
        st.subheader("Volume de Negociação")
        
        # Destaque visual: Pinta a barra do volume máximo de uma cor diferente
        # Criamos uma coluna de cores baseada na condição
        cores = ['#FF4B4B' if v == vol_max else '#00C8B3' for v in df['volume']]
        
        fig_vol = go.Figure(data=[go.Bar(
            x=df['data'], 
            y=df['volume'],
            marker_color=cores # Aplica a cor vermelha só na barra do recorde
        )])
        
        fig_vol.update_layout(
            height=300, 
            yaxis_tickprefix="$", 
            title="Destaque em vermelho para o dia de maior volume"
        )
        st.plotly_chart(fig_vol, use_container_width=True)

        # --- DADOS BRUTOS ---
        with st.expander("📥 Ver Dados Brutos e Baixar"):
            st.dataframe(df[['data', 'preco', 'volume']].sort_values('data', ascending=False))
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Baixar CSV", csv, f"{nome_moeda}.csv", "text/csv")

    else:
        st.error("Erro ao carregar dados.")

if __name__ == "__main__":
    main()