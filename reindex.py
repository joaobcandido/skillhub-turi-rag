import logging
from pathlib import Path
from src.data_loader import load_and_process_pdfs
from src.vector_store import index_chunks_in_chroma

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_DIR = Path(__file__).resolve().parent

def reindexar_base():
    logging.info("--- INICIANDO ROTINA DE REINDEXAÇÃO ---")
    
    # Define o caminho absoluto para a pasta dos PDFs
    pdf_folder = BASE_DIR / "data" / "pdfs"
    
    # Se os PDFs estiverem em outra pasta, substitua acima (ex: BASE_DIR / "data" / "pdfs")
    
    logging.info("Iniciando processamento e extração de PDFs...")
    chunks = load_and_process_pdfs(pdf_folder)
    
    if not chunks:
        logging.error(f"Nenhum chunk foi gerado! Verifique se os arquivos .pdf estão na pasta: {pdf_folder}")
        return

    logging.info(f"Processamento finalizado. Total de {len(chunks)} chunks gerados.")
    index_chunks_in_chroma(chunks=chunks)

if __name__ == "__main__":
    reindexar_base()
