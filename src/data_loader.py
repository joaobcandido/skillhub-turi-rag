import os
import re
import json
import logging
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Configuração de logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_DIR = os.path.join(BASE_DIR, 'data', 'pdfs')
OUTPUT_DIR = os.path.join(BASE_DIR, 'data', 'processed')

# Mapeamento de categorias com base no nome do arquivo
CATEGORY_MAP = {
    "generated_pdfs_Manual_de_Planos_e_Assinaturas.pdf": "Suporte",
    "generated_pdfs_Guia_de_Emissao_de_Certificados_e_Desafios.pdf": "Pedagógico",
    "generated_pdfs_Termos_de_Uso_e_Codigo_de_Conduta.pdf": "Fórum",
    "generated_pdfs_Manual_do_Tutor_e_Atendimento.pdf": "RH"
}

def clean_text(text: str) -> str:
    """Limpa ruídos de cabeçalhos, rodapés, paginação e espaços múltiplos."""
    # Remove cabeçalho e rodapé dos documentos oficiais
    text = re.sub(r'Skill\s*Hub\s*Platform\s*-\s*Documento\s*Oficial', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Página\s*\d+\s*de\s*\d+', '', text, flags=re.IGNORECASE)
    
    # Remove múltiplos espaços em branco e quebras de linha duplicadas
    text = re.sub(r'\n\s*\n', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    
    return text.strip()

def load_and_process_pdfs(pdf_folder):
    """Lê PDFs página por página, aplica limpeza e enriquece metadados."""
    documents_with_meta = []

    if not os.path.exists(pdf_folder):
        logging.error(f"Pasta {pdf_folder} não encontrada.")
        return documents_with_meta

    for filename in os.listdir(pdf_folder):
        if filename.endswith(".pdf"):
            filepath = os.path.join(pdf_folder, filename)
            category = CATEGORY_MAP.get(filename, "Geral")
            
            try:
                reader = PdfReader(filepath)
                for page_idx, page in enumerate(reader.pages):
                    raw_text = page.extract_text() or ""
                    cleaned_text = clean_text(raw_text)
                    
                    if cleaned_text:
                        documents_with_meta.append({
                            "text": cleaned_text,
                            "metadata": {
                                "source_file": filename,
                                "category": category,
                                "page_number": page_idx + 1
                            }
                        })
            except Exception as e:
                logging.error(f"Erro ao processar {filename}: {e}")

    return documents_with_meta

def generate_chunks(documents):
    """Aplica o RecursiveCharacterTextSplitter para chunking semântico."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    
    all_chunks = []
    chunk_counter = 0

    for doc in documents:
        splits = text_splitter.split_text(doc["text"])
        for chunk_text_content in splits:
            chunk_counter += 1
            all_chunks.append({
                "id": f"chunk_{chunk_counter}",
                "text": chunk_text_content,
                "metadata": doc["metadata"]
            })

    return all_chunks

def main():
    logging.info("Iniciando Pipeline do Card 2: Processamento e Extração...")
    
    # 1. Leitura + Limpeza + Metadados
    raw_docs = load_and_process_pdfs(PDF_DIR)
    logging.info(f"Páginas extraídas e limpas: {len(raw_docs)}")

    # 2. Chunking com RecursiveCharacterTextSplitter
    chunks = generate_chunks(raw_docs)
    logging.info(f"Total de Chunks gerados: {len(chunks)}")

    # 3. Salvar Output Processado
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, 'processed_chunks.json')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, ensure_ascii=False, indent=4)

    logging.info(f"Processamento concluído com sucesso! Arquivo salvo em: {output_path}")

if __name__ == "__main__":
    main()
