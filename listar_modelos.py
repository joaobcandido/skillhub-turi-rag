import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai

# Garante o caminho correto do .env na raiz
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / '.env'

load_dotenv(dotenv_path=ENV_PATH)

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

if not api_key:
    print(f"Erro: Chave não encontrada no arquivo .env localizado em: {ENV_PATH}")
else:
    print(f"Chave encontrada! Listando modelos suportados...\n")
    client = genai.Client(api_key=api_key)
    
    for model in client.models.list():
        # Exibe o nome limpo do modelo
        model_id = model.name.replace("models/", "")
        print(f"- {model_id}")
