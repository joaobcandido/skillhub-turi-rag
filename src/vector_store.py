import os
import json
import logging
import requests
from pathlib import Path
from dotenv import load_dotenv
import chromadb

# 1. Configuração de Caminhos da Raiz do Projeto
BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_FILE = BASE_DIR / 'data' / 'processed' / 'processed_chunks.json'
CHROMA_PATH = BASE_DIR / 'data' / 'chroma_db'
ENV_PATH = BASE_DIR / '.env'

# 2. Carrega as Variáveis do arquivo .env
load_dotenv(dotenv_path=ENV_PATH)

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Modelo de Embedding oficial e suportado
EMBEDDING_MODEL = "text-embedding-001"


def get_api_key():
    """Recupera a chave de API do Gemini."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(f"Nenhuma chave foi encontrada no arquivo .env em: {ENV_PATH}")
    return api_key


# 1. Defina o nome oficial do modelo atualizado
EMBEDDING_MODEL = "gemini-embedding-001"


def generate_embedding(text: str, api_key: str, is_query: bool = False) -> list:
    """Gera o embedding utilizando a chamada oficial REST do Gemini."""
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
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code != 200:
        raise RuntimeError(f"Erro na API do Gemini ({response.status_code}): {response.text}")
        
    data = response.json()
    return data["embedding"]["values"]


def load_chunks():
    """Carrega os chunks processados do arquivo JSON se nenhum chunk for passado."""
    if not os.path.exists(PROCESSED_FILE):
        raise FileNotFoundError(
            f"Arquivo não encontrado: {PROCESSED_FILE}. Execute o processamento de PDFs primeiro."
        )

    with open(PROCESSED_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def index_chunks_in_chroma(chunks: list = None):
    """
    Indexa os chunks no ChromaDB gerando embeddings.
    Pode receber uma lista de chunks ou carregar direto do arquivo JSON.
    """
    api_key = get_api_key()
    
    if chunks is None:
        chunks = load_chunks()

    logging.info(f"Carregando {len(chunks)} chunks para indexação vetorial...")

    # Inicializa o banco ChromaDB persistente em disco
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_PATH))

    # Recria a coleção 'skillhub_knowledge' do zero
    collection_name = "skillhub_knowledge"
    if collection_name in [c.name for c in chroma_client.list_collections()]:
        chroma_client.delete_collection(name=collection_name)

    collection = chroma_client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )

    ids = []
    documents = []
    metadatas = []
    embeddings = []

    for idx, item in enumerate(chunks):
        # Tenta pegar 'id' ou 'chunk_id'; se não existir, gera um ID sequencial
        chunk_id = item.get("id") or item.get("chunk_id") or f"chunk_{idx + 1}"
        text_content = item.get("text") or item.get("content") or ""
        metadata = item.get("metadata", {})

        # Gerar Embedding chamando a API oficial
        vector = generate_embedding(text_content, api_key, is_query=False)

        ids.append(chunk_id)
        documents.append(text_content)
        metadatas.append(metadata)
        embeddings.append(vector)

        logging.info(f"Chunk '{chunk_id}' -> Vetor gerado com sucesso ({len(vector)} dimensões).")

    # Inserir tudo no ChromaDB
    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings
    )

    logging.info(f"Sucesso! {len(ids)} vetores foram armazenados em: {CHROMA_PATH}")
    return collection, api_key


def build_vector_store():
    """Alias/Atalho para index_chunks_in_chroma."""
    return index_chunks_in_chroma()


def test_vector_search(collection, api_key, query="Como funciona o reembolso de planos?"):
    """Valida a busca vetorial por similaridade semântica."""
    logging.info(f"\n🔍 Executando teste de busca para: '{query}'")

    query_vector = generate_embedding(query, api_key, is_query=True)

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=2
    )

    print("\n--- RESULTADOS DA BUSCA POR SIMILARIDADE ---")
    for i in range(len(results["ids"][0])):
        chunk_id = results["ids"][0][i]
        doc_text = results["documents"][0][i]
        meta = results["metadatas"][0][i]
        distance = results["distances"][0][i]

        print(f"\n[Resultado {i+1}] - ID: {chunk_id} | Distância Cossenoidal: {distance:.4f}")
        print(f" Fonte: {meta.get('source_file')} | Categoria: {meta.get('category')} | Pág: {meta.get('page_number')}")
        print(f" Trecho: {doc_text[:150]}...")


def main():
    collection, api_key = build_vector_store()
    test_vector_search(collection, api_key)


if __name__ == "__main__":
    main()
