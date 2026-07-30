import os
import logging
import requests
from pathlib import Path
from dotenv import load_dotenv
import chromadb

# 1. Configuração de Caminhos da Raiz do Projeto
BASE_DIR = Path(__file__).resolve().parent.parent
CHROMA_PATH = BASE_DIR / 'data' / 'chroma_db'
ENV_PATH = BASE_DIR / '.env'

# 2. Carrega Variáveis de Ambiente
load_dotenv(dotenv_path=ENV_PATH)

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Modelo oficial de Embedding
EMBEDDING_MODEL = "gemini-embedding-001"


def get_api_key():
    """Recupera a chave de API do Gemini."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(f"Nenhuma chave foi encontrada no arquivo .env em: {ENV_PATH}")
    return api_key


def generate_embedding(text: str, api_key: str) -> list:
    """Gera o embedding para a pergunta do usuário."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{EMBEDDING_MODEL}:embedContent?key={api_key}"
    payload = {
        "model": f"models/{EMBEDDING_MODEL}",
        "content": {
            "parts": [{"text": text}]
        }
    }
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        raise RuntimeError(f"Erro ao gerar embedding ({response.status_code}): {response.text}")
        
    return response.json()["embedding"]["values"]


def retrieve_context(query: str, top_k: int = 3, category_filter: str = None) -> dict:
    """
    Executa a busca por similaridade semântica no ChromaDB com suporte a filtros por metadados.
    
    :param query: Pergunta feita pelo usuário.
    :param top_k: Número de trechos relevantes a serem retornados.
    :param category_filter: Categoria para filtragem (ex: 'Suporte', 'Pedagógico', 'RH').
    :return: Dicionário contendo os documentos recuperados e o bloco de contexto formatado.
    """
    api_key = get_api_key()
    
    # 1. Vetorização da Consulta
    logging.info(f"Vetorizando a pergunta: '{query}'")
    query_vector = generate_embedding(query, api_key)

    # 2. Conexão com o ChromaDB
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    collection = chroma_client.get_collection(name="skillhub_knowledge")

    # 3. Montagem do Filtro de Metadados (se fornecido)
    where_clause = None
    if category_filter:
        where_clause = {"category": category_filter}
        logging.info(f"Aplicando filtro por categoria: '{category_filter}'")

    # 4. Busca por Similaridade Semântica
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        where=where_clause
    )

    retrieved_docs = []
    formatted_context_blocks = []

    # 5. Montagem do Bloco de Contexto
    if results and results["documents"] and len(results["documents"][0]) > 0:
        for i in range(len(results["ids"][0])):
            chunk_id = results["ids"][0][i]
            doc_text = results["documents"][0][i]
            meta = results["metadatas"][0][i]
            distance = results["distances"][0][i]

            doc_info = {
                "id": chunk_id,
                "text": doc_text,
                "source_file": meta.get("source_file", "Desconhecido"),
                "category": meta.get("category", "Geral"),
                "page_number": meta.get("page_number", "-"),
                "distance": distance
            }
            retrieved_docs.append(doc_info)

            # Formatação estruturada do trecho para injeção no Prompt
            block = (
                f"--- TRECHO {i+1} ---\n"
                f"Fonte: {doc_info['source_file']} (Pág. {doc_info['page_number']}) | Categoria: {doc_info['category']}\n"
                f"Conteúdo:\n{doc_text}\n"
            )
            formatted_context_blocks.append(block)

    full_context_text = "\n".join(formatted_context_blocks)

    return {
        "query": query,
        "documents": retrieved_docs,
        "context_text": full_context_text
    }


def buscar_contexto(pergunta: str, categoria_filtro: str = None, top_k: int = 3) -> str:
    """
    Função wrapper amigável para ser consumida por outros módulos (como o generator.py).
    Retorna apenas a string de contexto gerada.
    """
    resultado = retrieve_context(query=pergunta, top_k=top_k, category_filter=categoria_filtro)
    return resultado["context_text"]


def main():
    # Teste 1: Busca Semântica Geral
    test_query = "Como funciona o reembolso de planos?"
    logging.info("--- TESTE 1: Busca Semântica Padrão ---")
    retrieval_res = retrieve_context(query=test_query, top_k=3)

    print("\n================ BLOCO DE CONTEXTO GERADO ================")
    print(retrieval_res["context_text"])
    print("=========================================================\n")

    # Teste 2: Busca com Filtro por Metadados
    logging.info("--- TESTE 2: Busca com Filtro de Categoria (Suporte) ---")
    filtered_res = retrieve_context(query=test_query, top_k=2, category_filter="Suporte")
    print("\n================ CONTEXTO FILTRADO (SUPORTE) ================")
    print(filtered_res["context_text"])
    print("=============================================================")


if __name__ == "__main__":
    main()
