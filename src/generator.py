import os
import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from retriever import buscar_contexto

# 1. Carrega Variáveis de Ambiente do .env da raiz
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / '.env'
load_dotenv(dotenv_path=ENV_PATH)

# Chave de API
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError(f"Chave GEMINI_API_KEY não foi encontrada no .env em: {ENV_PATH}")

# Inicializa o cliente oficial
client = genai.Client(api_key=api_key)

MENSAGEM_FALLBACK = (
    "Ops! Não encontrei essa informação nos guias da SkillHub. "
    "Por favor, tente reformular sua pergunta ou entre em contato com o nosso suporte em suporte@skillhub.com."
)

SYSTEM_PROMPT = """
Você é o Turi, o assistente virtual amigável e prestativo da plataforma SkillHub.

Sua tarefa é responder às dúvidas dos alunos EXCLUSIVAMENTE utilizando o bloco de contexto fornecido abaixo.

REGRAS OBRIGATÓRIAS:
1. Responda APENAS com base nas informações do CONTEXTO. Não utilize conhecimentos prévios ou externos.
2. Se a informação necessária para responder à pergunta NÃO estiver presente no contexto, responda exatamente com a frase de fallback configurada.
3. CITAÇÃO DE FONTES: Sempre que responder com base no contexto, inclua a fonte e a página consultada ao final da resposta no formato:
   'Fonte: <nome_do_pdf> | Página <numero>'
4. Mantenha um tom amigável, claro e objetivo.
"""

def gerar_resposta(pergunta: str, categoria: str = None) -> str:
    # 1. Recupera o contexto do retriever
    contexto = buscar_contexto(pergunta, categoria_filtro=categoria)
    
    # 2. Mecanismo de Fallback por ausência de contexto
    if not contexto or len(str(contexto).strip()) == 0:
        return MENSAGEM_FALLBACK

    # 3. Monta o prompt do usuário
    prompt_usuario = f"""
    CONTEXTO RECUPERADO:
    {contexto}

    PERGUNTA DO ALUNO:
    {pergunta}
    """

    # 4. Chamada da API com a nova SDK (usando o modelo padrão de geração)
    response = client.models.generate_content(
        model='gemini-3.5-flash',
        contents=prompt_usuario,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.2,
        ),
    )
    
    return response.text

if __name__ == "__main__":
    print("\n--- TESTE 1: Pergunta dentro da base ---")
    res1 = gerar_resposta("Como funciona o reembolso do plano?")
    print(res1)

    print("\nAguardando 10 segundos para reset da quota da API...")
    time.sleep(10)

    print("--- TESTE 2: Pergunta fora da base (Fallback) ---")
    res2 = gerar_resposta("Como faço para tirar carteira de motorista?")
    print(res2)
