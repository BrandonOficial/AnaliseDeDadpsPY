import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go # Adicionado para customizações extras

# --- Configuração Básica ---
st.set_page_config(layout="centered", page_title="Crypto Simples +")

# --- Função de Pegar Dados (Agora busca Volume também) ---
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
        
        # 2. Volumes (Novidade)
        df_vol = pd.DataFrame(dados['total_volumes'], columns=['timestamp', 'volume'])
        
        # Junta tudo (Merge)
        df_final = pd.merge(df, df_vol, on='timestamp')
        
        # 3. Cria Média Móvel (Cálculo simples)
        df_final['media_movel'] = df_final['preco'].rolling(window=7).mean()
        
        return df_final
    except:
        return pd.DataFrame()

# --- Interface do Usuário ---
def main():
    st.title("🎯 Monitor de Cripto Simplificado")
    
    # --- BARRA LATERAL ---
    st.sidebar.header("Configurações")
    opcoes = {"Bitcoin": "bitcoin", "Ethereum": "ethereum", "Solana": "solana", "Ripple": "ripple"}
    nome_moeda = st.sidebar.selectbox("Moeda", list(opcoes.keys()))
    dias = st.sidebar.radio("Período", ["30", "90", "365"], index=0, horizontal=True)
    
    # Checkbox para ativar funcionalidades extras sem poluir
    mostrar_media = st.sidebar.checkbox("Mostrar Média Móvel (7d)")
    
    id_moeda = opcoes[nome_moeda]
    
    # --- DADOS ---
    df = pegar_dados_completos(id_moeda, dias)
    
    if not df.empty:
        # Cálculos para os Cartões
        preco_atual = df['preco'].iloc[-1]
        preco_inicio = df['preco'].iloc[0]
        variacao = ((preco_atual - preco_inicio) / preco_inicio) * 100
        vol_medio = df['volume'].mean()
        
        # --- 1. CARTÕES (Adicionei Volume Médio) ---
        col1, col2, col3 = st.columns(3)
        col1.metric("Preço Atual", f"$ {preco_atual:,.2f}")
        col2.metric("Variação", f"{variacao:.2f}%", delta_color="normal")
        col3.metric("Volume Médio", f"$ {vol_medio:,.0f}") # Sem centavos para caber melhor
        
        st.divider()

        # --- 2. GRÁFICO PRINCIPAL (Preço) ---
        fig = px.area(
            df, x='data', y='preco',
            title=f"Evolução do Preço: {nome_moeda}",
            labels={'data': 'Data', 'preco': 'Preço (USD)'}
        )
        fig.update_traces(line_color='#8257E5') # Roxo Nubank/Twitch
        
        # Se o usuário marcou o checkbox, adicionamos a linha da média
        if mostrar_media:
            fig.add_trace(go.Scatter(
                x=df['data'], y=df['media_movel'],
                mode='lines', name='Média 7 Dias',
                line=dict(color='orange', width=2, dash='dot')
            ))

        fig.update_layout(yaxis_tickprefix="$", hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
        
        # --- 3. GRÁFICO SECUNDÁRIO (Volume) ---
        # Colocamos logo abaixo, menorzinho, para dar contexto
        st.subheader("Volume de Negociação")
        fig_vol = px.bar(df, x='data', y='volume', color_discrete_sequence=['#00C8B3'])
        fig_vol.update_layout(height=300, yaxis_tickprefix="$") # Altura fixa menor (300px)
        st.plotly_chart(fig_vol, use_container_width=True)

        # --- 4. DADOS E DOWNLOAD ---
        # Usamos o 'expander' para não poluir a tela. Só abre se clicar.
        with st.expander("📥 Ver Dados Brutos e Baixar"):
            st.dataframe(df[['data', 'preco', 'volume', 'media_movel']].sort_values('data', ascending=False))
            
            # Botão de Download
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Baixar planilha (CSV)",
                data=csv,
                file_name=f"{nome_moeda}_dados.csv",
                mime='text/csv',
            )

    else:
        st.error("Erro ao carregar dados. Tente novamente mais tarde.")

if __name__ == "__main__":
    main()