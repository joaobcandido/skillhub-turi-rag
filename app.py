import streamlit as st
import sys
from pathlib import Path

# Adiciona o diretório 'src' ao PATH para importar as funções
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR / 'src'))

from src.generator import gerar_resposta
from quota_tracker import obter_uso_atual
from ingestor import processar_e_indexar_pdf, limpar_base_de_dados

# 1. Configuração da Página
st.set_page_config(
    page_title="Turi — Assistente Virtual SkillHub",
    page_icon="🤖",
    layout="centered"
)

# 🎨 ESTILIZAÇÃO CSS CUSTOMIZADA
st.markdown("""
<style>
    /* Força a cor verde em todos os botões primários da sidebar */
    [data-testid="stSidebar"] button[data-testid="baseButton-primary"] {
        background-color: #2e7d32 !important;
        background-image: none !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
    }
    
    [data-testid="stSidebar"] button[data-testid="baseButton-primary"]:hover {
        background-color: #1b5e20 !important;
        background-image: none !important;
        color: white !important;
    }

    /* Fallback para versões com nomenclatura de tag antiga */
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background-color: #2e7d32 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# ⚙️ BARRA LATERAL (SIDEBAR)
# ---------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Painel do Sistema")
    st.markdown("---")
    
    # 📊 BLOCO 1: CONTADOR DE COTA DO GEMINI
    st.subheader("📊 Uso da Cota Gemini (Hoje)")
    uso = obter_uso_atual()
    st.metric(
        label="Requisições Realizadas", 
        value=f"{uso['total']} / {uso['limite']}",
        delta=f"{uso['porcentagem']}% do limite",
        delta_color="inverse"
    )
    st.progress(uso['porcentagem'] / 100)
    st.caption("ℹ️ Limite do Free Tier estimado em 1.500 requisições/dia. Renovado diariamente às 21h.")
    st.markdown("---")

    # Inicializa a chave do uploader na sessão para permitir a limpeza automática
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0

    # 📁 BLOCO 2: UPLOAD DE NOVOS MANUAIS (PDF)
    st.subheader("📁 Adicionar Novo Manual (PDF)")
    arquivo_pdf = st.file_uploader(
        "Envie um PDF para expandir o conhecimento do Turi:", 
        type=["pdf"],
        key=f"pdf_uploader_{st.session_state.uploader_key}"
    )

    if arquivo_pdf is not None:
        if st.button("📥 Processar e Indexar PDF", type="primary", use_container_width=True):
            with st.spinner("Processando e indexando trechos no ChromaDB..."):
                sucesso, mensagem = processar_e_indexar_pdf(arquivo_pdf)
                if sucesso:
                    st.toast("Base de conhecimento atualizada com sucesso!", icon="✅")
                    # Reseta a caixa de upload incrementando a chave
                    st.session_state.uploader_key += 1
                    st.rerun()
                else:
                    st.error(mensagem)

    st.markdown("---")

    # 🗑️ BLOCO 3: LIMPEZA E ZERAR BASE DE DADOS
    st.subheader("🛠️ Manutenção da Base")
    if st.button("🗑️ Limpar Base de Dados", type="secondary", use_container_width=True):
        with st.spinner("Limpando ChromaDB e removendo PDFs..."):
            sucesso, mensagem = limpar_base_de_dados()
            if sucesso:
                st.toast(mensagem, icon="🗑️")
                # Reseta o histórico de conversas do chat
                st.session_state.messages = [
                    {
                        "role": "assistant",
                        "content": "Olá! Eu sou o **Turi**, assistente virtual da SkillHub. Como posso te ajudar hoje?"
                    }
                ]
                st.session_state.uploader_key += 1
                st.rerun()
            else:
                st.error(mensagem)

# 2. Título e Cabeçalho Principal
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
