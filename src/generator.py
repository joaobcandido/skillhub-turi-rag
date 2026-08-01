import os
import time
import logging
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ServerError, APIError, ClientError
from retriever import buscar_contexto
from quota_tracker import registrar_e_obter_uso

# 1. Configuração dos Caminhos e Logs
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / '.env'
load_dotenv(dotenv_path=ENV_PATH)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError(f"Chave GEMINI_API_KEY não encontrada no .env em: {ENV_PATH}")

# Inicializa o cliente da SDK nova
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
    # 0. Filtro rápido para saudações genéricas (economiza cota e requisições)
    saudacoes = ["ola", "olá", "oi", "bom dia", "boa tarde", "boa noite"]
    if pergunta.strip().lower() in saudacoes:
        return (
            "Olá! Sou o Turi, assistente virtual da SkillHub. "
            "Como posso ajudar com suas dúvidas sobre nossos cursos, planos e diretrizes hoje?"
        )

    # 1. Recupera o contexto do retriever
    contexto = buscar_contexto(pergunta, categoria_filtro=categoria)
    
    # 2. Mecanismo de Fallback por ausência de contexto
    if not contexto or len(str(contexto).strip()) == 0:
        return MENSAGEM_FALLBACK

    # 3. Monta o prompt
    prompt_usuario = f"""
    CONTEXTO RECUPERADO:
    {contexto}

    PERGUNTA DO ALUNO:
    {pergunta}
    """

    # 4. Chamada segura com tratamento de erros e rastreamento de cota
    try:
        response = client.models.generate_content(
            model='gemini-flash-latest',  # Modelo estável com cota liberada
            contents=prompt_usuario,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.2,
            ),
        )

        # Registra a chamada bem-sucedida no contador de cotas
        uso_atual = registrar_e_obter_uso()
        logging.info(f"📊 Chamada concluída com sucesso. Uso do dia: {uso_atual['total']}/{uso_atual['limite']}")

        return response.text

    except (ClientError, ServerError, APIError) as e:
        erro_str = str(e)
        if "429" in erro_str or "RESOURCE_EXHAUSTED" in erro_str:
            logging.warning(f"[COTA EXCEDIDA 429]: {e}")
            return (
                "⏳ Limite de requisições por minuto atingido no plano do Gemini. "
                "Por favor, aguarde cerca de 30 a 60 segundos e tente sua pergunta novamente."
            )
        
        logging.error(f"[GEMINI API ERRO]: {e}")
        return (
            "⚠️ O servidor da IA está enfrentando alta demanda e ficou temporariamente indisponível. "
            "Por favor, tente enviar sua pergunta novamente em alguns instantes."
        )
    except Exception as e:
        logging.error(f"[ERRO INESPERADO GENERATOR]: {e}")
        return "Ops! Ocorreu um erro ao gerar a resposta. Por favor, tente novamente."

if __name__ == "__main__":
    print("\n--- TESTE: Pergunta de Reembolso ---")
    res = gerar_resposta("Como funciona o reembolso do plano?")
    print(res)
