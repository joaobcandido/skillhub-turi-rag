import os
import logging
import requests
from pathlib import Path
from dotenv import load_dotenv
from pypdf import PdfReader
import chromadb

# 1. Configuração de Caminhos da Raiz do Projeto
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "pdfs"
CHROMA_PATH = BASE_DIR / "data" / "chroma_db"
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Modelo de Embedding oficial configurado no seu vector_store
EMBEDDING_MODEL = "gemini-embedding-001"

def obter_api_key():
    """Recupera a chave de API buscando do Streamlit Secrets ou do .env."""
    try:
        import streamlit as st
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
        if "GOOGLE_API_KEY" in st.secrets:
            return st.secrets["GOOGLE_API_KEY"]
    except Exception:
        pass

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    return api_key

def gerar_embedding_gemini(text: str, api_key: str, is_query: bool = False) -> list:
    """Gera o embedding utilizando exatamente a mesma chamada REST do vector_store."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{EMBEDDING_MODEL}:embedContent?key={api_key}"
    
    task_type = "RETRIEVAL_QUERY" if is_query else "RETRIEVAL_DOCUMENT"
    
    payload = {
        "model": f"models/{EMBEDDING_MODEL}",
        "content": {
            "parts": [{"text": text}]
        },
        "taskType": task_type
    }
    
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    
    if response.status_code != 200:
        raise RuntimeError(f"Erro na API do Gemini ({response.status_code}): {response.text}")
        
    data = response.json()
    return data["embedding"]["values"]

def processar_e_indexar_pdf(uploaded_file) -> tuple[bool, str]:
    """Salva o PDF enviado e insere os vetores diretamente na coleção 'skillhub_knowledge'."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        nome_original = uploaded_file.name if hasattr(uploaded_file, "name") else Path(uploaded_file).name
        nome_arquivo = f"generated_pdfs_{nome_original}"
        pdf_path = DATA_DIR / nome_arquivo

        if hasattr(uploaded_file, "getbuffer"):
            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

        api_key = obter_api_key()
        if not api_key:
            return False, "Chave de API (GEMINI_API_KEY ou GOOGLE_API_KEY) não encontrada."

        # Extração de texto
        reader = PdfReader(pdf_path)
        chunks = []
        metadados = []
        embeddings = []
        ids = []

        chunk_id = 0
        for num_pagina, pagina in enumerate(reader.pages, start=1):
            texto = pagina.extract_text()
            if not texto or len(texto.strip()) == 0:
                continue

            tamanho_bloco = 800
            overlap = 100
            start = 0
            
            while start < len(texto):
                fim = min(start + tamanho_bloco, len(texto))
                trecho = texto[start:fim].strip()

                if len(trecho) > 30:
                    chunks.append(trecho)
                    metadados.append({
                        "source_file": nome_arquivo,
                        "category": "manual_pdf",
                        "page_number": num_pagina
                    })
                    ids.append(f"upload_{nome_original}_p{num_pagina}_c{chunk_id}")
                    
                    # Gerando embedding idêntico ao vector_store
                    vector = gerar_embedding_gemini(trecho, api_key, is_query=False)
                    embeddings.append(vector)
                    
                    chunk_id += 1

                start += tamanho_bloco - overlap

        if not chunks:
            return False, "O PDF enviado não possui texto extraível."

        # Conecta à coleção oficial do seu projeto
        chroma_client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        
        # Pega a coleção 'skillhub_knowledge' existente
        collection = chroma_client.get_or_create_collection(
            name="skillhub_knowledge",
            metadata={"hnsw:space": "cosine"}
        )

        collection.add(
            ids=ids,
            documents=chunks,
            metadatas=metadados,
            embeddings=embeddings
        )

        logging.info(f"PDF '{nome_original}' indexado com sucesso na coleção skillhub_knowledge.")
        return True, f"PDF **'{nome_original}'** processado e indexado com sucesso! ({len(chunks)} trechos adicionados)."

    except Exception as e:
        logging.error(f"Erro ao processar PDF: {e}")
        return False, f"Erro ao processar o PDF: {str(e)}"

def limpar_base_de_dados() -> tuple[bool, str]:
    """Apaga todos os registros da coleção skillhub_knowledge no ChromaDB e exclui os PDFs gravados."""
    try:
        # 1. Limpa a coleção no ChromaDB
        chroma_client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        collection_name = "skillhub_knowledge"
        
        # Se a coleção existir, apaga e recria vazia
        if collection_name in [c.name for c in chroma_client.list_collections()]:
            chroma_client.delete_collection(name=collection_name)
            
        chroma_client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        # 2. Apaga os arquivos do diretório data/pdfs
        if DATA_DIR.exists():
            for arquivo in DATA_DIR.glob("*"):
                if arquivo.is_file():
                    arquivo.unlink()

        logging.info("Base de dados e PDFs limpos com sucesso.")
        return True, "Base de dados e arquivos PDFs limpos com sucesso!"

    except Exception as e:
        logging.error(f"Erro ao limpar base de dados: {e}")
        return False, f"Erro ao limpar a base de dados: {str(e)}"

if __name__ == "__main__":
    arquivo_teste = BASE_DIR / "Catalogo_de_Cursos_SkillHub.pdf"
    if arquivo_teste.exists():
        print(f"🚀 Processando arquivo local via terminal: {arquivo_teste.name}")
        sucesso, msg = processar_e_indexar_pdf(arquivo_teste)
        print(f"Resultado: {msg}")
    else:
        print("⚠️ Arquivo de teste não encontrado na raiz.")
