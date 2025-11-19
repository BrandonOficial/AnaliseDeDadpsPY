import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# --- Configuração Básica ---
st.set_page_config(layout="centered", page_title="Crypto Simples")

# --- Função Única de Pegar Dados (O Coração do App) ---
@st.cache_data(ttl=300) # Cache de 5 min
def pegar_dados_simples(moeda_id, dias):
    try:
        # Usando a API simples de histórico
        url = f"https://api.coingecko.com/api/v3/coins/{moeda_id}/market_chart"
        params = {'vs_currency': 'usd', 'days': dias, 'interval': 'daily'}
        
        resposta = requests.get(url, params=params)
        dados = resposta.json()
        
        # Transforma a lista de preços em Tabela (DataFrame)
        df = pd.DataFrame(dados['prices'], columns=['timestamp', 'preco'])
        df['data'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        return df
    except:
        return pd.DataFrame()

# --- Interface do Usuário ---
def main():
    st.title("🎯 Monitor de Cripto Simplificado")
    
    # 1. Barra Lateral Simples
    st.sidebar.header("Escolha sua Moeda")
    opcoes = {"Bitcoin": "bitcoin", "Ethereum": "ethereum", "Solana": "solana"}
    nome_moeda = st.sidebar.selectbox("Moeda", list(opcoes.keys()))
    dias = st.sidebar.radio("Período", ["7", "30", "90", "365"], index=1, horizontal=True)
    
    id_moeda = opcoes[nome_moeda]
    
    # 2. Buscando os dados
    df = pegar_dados_simples(id_moeda, dias)
    
    if not df.empty:
        # Pegando valores para mostrar nos cartões
        preco_atual = df['preco'].iloc[-1]  # Último preço da lista
        preco_inicio = df['preco'].iloc[0]  # Primeiro preço da lista
        variacao = ((preco_atual - preco_inicio) / preco_inicio) * 100
        
        # 3. Cartões de Informação (Métricas)
        col1, col2, col3 = st.columns(3)
        col1.metric("Preço Atual", f"$ {preco_atual:,.2f}")
        col2.metric("Variação no Período", f"{variacao:.2f}%", delta_color="normal") # Verde/Vermelho auto
        col3.metric("Máxima Atingida", f"$ {df['preco'].max():,.2f}")
        
        st.divider()

        # 4. Gráfico de Área (Mais limpo que velas)
        fig = px.area(
            df, 
            x='data', 
            y='preco',
            title=f"Evolução do {nome_moeda}",
            labels={'data': 'Data', 'preco': 'Preço (USD)'}
        )
        
        # Ajustes visuais para ficar bonitão
        fig.update_traces(line_color='#8257E5') # Roxo bonito
        fig.update_layout(yaxis_tickprefix="$") # Coloca o $ no eixo Y
        
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.error("Erro ao carregar dados. A API pode estar ocupada.")

if __name__ == "__main__":
    main()