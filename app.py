# app.py

import streamlit as st
import pandas as pd
import google.generativeai as genai
import sys
from io import StringIO

# --- Configuração da Página e Título ---
st.set_page_config(page_title="Analisador de Dados com IA", page_icon="🤖", layout="wide")
st.title("🤖 Analisador de Dados com IA")
st.caption("Carregue sua planilha e faça perguntas para obter respostas conclusivas.")

# --- Configuração da API Key e do Modelo ---
# Para DEPLOY: A chave será lida dos Segredos do Streamlit (st.secrets)
# Para rodar LOCALMENTE: Descomente a linha abaixo e cole sua chave
# GOOGLE_API_KEY = "SUA_CHAVE_API_AQUI" 

try:
    # Tenta obter a chave do ambiente de deploy do Streamlit
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except (FileNotFoundError, KeyError):
    # Se não encontrar, assume que estamos rodando localmente
    st.warning("Chave de API não encontrada nos Segredos. Verifique sua configuração local caso o app não funcione.")

# Configura o genai apenas se a chave estiver disponível
if 'GOOGLE_API_KEY' in locals() or 'GOOGLE_API_KEY' in st.secrets:
    api_key = st.secrets.get("GOOGLE_API_KEY", locals().get("GOOGLE_API_KEY"))
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

# --- Inicialização do Estado da Sessão (A "MEMÓRIA" DO APP) ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "df" not in st.session_state:
    st.session_state.df = None
if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[]) if model else None

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
            
            # Limpa o histórico de chat ao carregar um novo arquivo
            st.session_state.messages = []
            if model:
                st.session_state.chat = model.start_chat(history=[])

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

        # Prepara e envia o prompt para a IA
        with st.chat_message("assistant"):
            with st.spinner("Analisando os dados e preparando sua resposta..."):
                
                # NOVO PROMPT MELHORADO
                # Envia uma amostra dos dados e instruções claras para a IA
                df_sample = st.session_state.df.head().to_csv(index=False)
                
                full_prompt = f"""
                Você é um assistente de análise de dados sênior. Sua tarefa é analisar a planilha do usuário e responder de forma direta e conclusiva.

                **Contexto dos Dados:**
                O usuário carregou uma planilha. Aqui estão as primeiras linhas para seu contexto:
                ```csv
                {df_sample}
                ```

                **Instruções Críticas:**
                1.  **Seja Conclusivo:** Aja como se você já tivesse executado toda a análise necessária nos dados completos.
                2.  **NÃO descreva o processo:** Não explique o código Pandas que você usaria. Não diga "Para descobrir isso, eu faria...".
                3.  **Forneça a Resposta Final:** Vá direto ao ponto e entregue a informação que o usuário pediu. Se a pergunta for "Qual o produto mais vendido?", sua resposta deve começar com "O produto mais vendido é...".

                **Pergunta do Usuário:** "{prompt}"
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
    if not model:
        st.error("A API Key do Google não foi configurada. Por favor, adicione-a nos Segredos do Streamlit para o app funcionar.")
    st.info("Por favor, carregue uma planilha na barra lateral para começar a análise.")
