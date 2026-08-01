import json
import logging
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
QUOTA_FILE = DATA_DIR / "quota_tracker.json"

# Limite estipulado do Free Tier diário para o Gemini Flash
LIMITE_DIARIO_ESTIMADO = 1500

def registrar_e_obter_uso() -> dict:
    """Registra uma nova chamada da API e retorna o estado atual do consumo."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    hoje = datetime.now().strftime("%Y-%m-%d")
    
    dados = {"data": hoje, "total_chamadas": 0}
    
    if QUOTA_FILE.exists():
        try:
            with open(QUOTA_FILE, "r", encoding="utf-8") as f:
                dados = json.load(f)
        except Exception as e:
            logging.error(f"Erro ao ler quota_tracker.json: {e}")

    # Se virou o dia, reseta o contador
    if dados.get("data") != hoje:
        dados["data"] = hoje
        dados["total_chamadas"] = 0

    dados["total_chamadas"] += 1

    try:
        with open(QUOTA_FILE, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=2)
    except Exception as e:
        logging.error(f"Erro ao salvar quota_tracker.json: {e}")

    return obter_uso_atual()


def obter_uso_atual() -> dict:
    """Retorna os dados atuais de consumo sem incrementar a contagem."""
    hoje = datetime.now().strftime("%Y-%m-%d")
    dados = {"data": hoje, "total_chamadas": 0}

    if QUOTA_FILE.exists():
        try:
            with open(QUOTA_FILE, "r", encoding="utf-8") as f:
                dados_salvos = json.load(f)
                if dados_salvos.get("data") == hoje:
                    dados = dados_salvos
        except Exception:
            pass

    total = dados["total_chamadas"]
    porcentagem = min(round((total / LIMITE_DIARIO_ESTIMADO) * 100, 1), 100.0)

    return {
        "data": hoje,
        "total": total,
        "limite": LIMITE_DIARIO_ESTIMADO,
        "porcentagem": porcentagem
    }
