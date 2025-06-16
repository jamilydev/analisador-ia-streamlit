# app.py

import streamlit as st
import pandas as pd
import google.generativeai as genai
import sys
from io import StringIO

# --- Configuração da Página e Título ---
st.set_page_config(page_title="Analisador de Planilhas com IA", page_icon="🤖", layout="wide")
st.title("🤖 Analisador de Planilhas com IA")
st.caption(f"Hoje é {pd.Timestamp.now(tz='America/Sao_Paulo').strftime('%A, %d de %B de %Y')}")

# --- Configuração da API Key e do Modelo ---
# Para DEPLOY: A chave será lida dos Segredos do Streamlit (st.secrets)
# Para rodar LOCALMENTE: Descomente a linha abaixo e cole sua chave
# GOOGLE_API_KEY = "SUA_CHAVE_API_AQUI" 

try:
    # Tenta obter a chave do ambiente de deploy do Streamlit
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except FileNotFoundError:
    # Se não encontrar, assume que estamos rodando localmente
    st.warning("Chave de API não encontrada nos Segredos. Verifique sua configuração local.")
    # Se você definiu a chave manualmente acima, o código continuará.

if 'GOOGLE_API_KEY' in locals() or 'GOOGLE_API_KEY' in st.secrets:
    genai.configure(api_key=st.secrets.get("GOOGLE_API_KEY", locals().get("GOOGLE_API_KEY")))
    model = genai.GenerativeModel('gemini-1.5-flash')


# --- Inicialização do Estado da Sessão (A "MEMÓRIA" DO APP) ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "df" not in st.session_state:
    st.session_state.df = None
if "chat" not in st.session_state:
    # Inicia o chat com o modelo se a chave API estiver disponível
    if 'GOOGLE_API_KEY' in locals() or 'GOOGLE_API_KEY' in st.secrets:
        st.session_state.chat = model.start_chat(history=[])
    else:
        st.session_state.chat = None

# --- Barra Lateral (Sidebar) para Upload ---
with st.sidebar:
    st.header("1. Carregue seus Dados")
    uploaded_file = st.file_uploader("Selecione sua planilha (.xlsx ou .csv)", type=["xlsx", "csv"])
    
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.xlsx'):
                st.session_state.df = pd.read_excel(uploaded_file)
            else:
                st.session_state.df = pd.read_csv(uploaded_file)
            
            st.success("Arquivo carregado!")
            st.dataframe(st.session_state.df.head(), height=220)
        except Exception as e:
            st.error(f"Erro ao ler o arquivo: {e}")
            st.session_state.df = None


# --- Interface Principal do Chat ---
if st.session_state.df is not None:
    st.header("2. Converse com seus Dados")

    # Mostra o histórico da conversa
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Captura a nova pergunta do usuário
    if prompt := st.chat_input("Qual sua pergunta sobre a planilha?"):
        # Adiciona a pergunta do usuário ao histórico e exibe na tela
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Prepara a resposta do assistente
        with st.chat_message("assistant"):
            with st.spinner("Analisando e pensando..."):
                # Prepara um prompt mais completo para a IA, dando o contexto
                full_prompt = f"""
                Contexto: Você é um assistente de análise de dados. O usuário carregou uma planilha.
                As colunas são: {', '.join(st.session_state.df.columns)}.
                O DataFrame completo está disponível para você como `df`.

                Pergunta do usuário: "{prompt}"

                Sua tarefa é responder à pergunta do usuário. Se a pergunta exigir uma operação com os dados (soma, média, filtro, etc.),
                mentalmente gere o código pandas para encontrar a resposta e então me diga o resultado em linguagem natural e amigável.
                """
                
                # Envia a pergunta para o chat e obtém a resposta
                if st.session_state.chat:
                    response = st.session_state.chat.send_message(full_prompt)
                    response_text = response.text
                else:
                    response_text = "ERRO: A sessão de chat não foi inicializada. Verifique a API Key."

                st.markdown(response_text)
        
        # Adiciona a resposta do assistente ao histórico
        st.session_state.messages.append({"role": "assistant", "content": response_text})
else:
    st.info("Por favor, carregue uma planilha na barra lateral para começar a análise.")