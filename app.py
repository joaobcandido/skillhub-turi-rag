import streamlit as st
import sys
from pathlib import Path

# Adiciona o diretório 'src' ao PATH para importar as funções
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR / 'src'))

from generator import gerar_resposta

# 1. Configuração da Página
st.set_page_config(
    page_title="Turi — Assistente Virtual SkillHub",
    page_icon="🤖",
    layout="centered"
)

# 2. Título e Cabeçalho
st.title("🤖 Turi — Assistente Virtual SkillHub")
st.caption("Tire suas dúvidas sobre cursos, matrículas, certificados e diretrizes da SkillHub.")

# 3. Inicialização do Histórico de Conversa na Sessão
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Olá! Eu sou o **Turi**, assistente virtual da SkillHub. Como posso te ajudar hoje?"
        }
    ]

# 4. Exibição do Histórico de Mensagens
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Exibe seção de fontes caso a mensagem contenha metadados de fontes
        if "sources" in message and message["sources"]:
            with st.expander("📚 Ver fontes consultadas"):
                for src in message["sources"]:
                    st.write(f"- 📄 `{src}`")
        
        # Botões de Feedback para respostas do assistente
        if message["role"] == "assistant" and idx > 0:
            col1, col2, _ = st.columns([1, 1, 10])
            with col1:
                if st.button("👍", key=f"like_{idx}"):
                    st.toast("Obrigado pelo feedback positivo!", icon="✅")
            with col2:
                if st.button("👎", key=f"dislike_{idx}"):
                    st.toast("Obrigado pelo feedback. Vamos melhorar!", icon="⚠️")

# 5. Entrada do Usuário
if user_input := st.chat_input("Digite sua pergunta aqui..."):
    # Adiciona pergunta do usuário ao histórico
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("user"):
        st.markdown(user_input)

    # Gera a resposta do Turi
    with st.chat_message("assistant"):
        with st.spinner("Turi está consultando os manuais..."):
            resposta_bruta = gerar_resposta(user_input)
            
            # Separa o conteúdo principal das citações de fonte
            linhas = resposta_bruta.split("\n")
            texto_resposta = []
            fontes_encontradas = []

            for linha in linhas:
                if linha.startswith("Fonte:"):
                    fontes_encontradas.append(linha.replace("Fonte:", "").strip())
                else:
                    texto_resposta.append(linha)

            resposta_limpa = "\n".join(texto_resposta)

            # Exibe o texto da resposta
            st.markdown(resposta_limpa)

            # Exibe o expansor de fontes
            if fontes_encontradas:
                with st.expander("📚 Ver fontes consultadas"):
                    for src in fontes_encontradas:
                        st.write(f"- 📄 `{src}`")

            # Armazena na sessão
            st.session_state.messages.append({
                "role": "assistant",
                "content": resposta_limpa,
                "sources": fontes_encontradas
            })
            st.rerun()
