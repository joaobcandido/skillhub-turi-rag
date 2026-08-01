from fpdf import FPDF, XPos, YPos

class PDF(FPDF):
    def __init__(self, titulo_cabecalho):
        super().__init__()
        self.titulo_cabecalho = titulo_cabecalho

    def header(self):
        self.set_font('helvetica', 'B', 14)
        self.cell(0, 10, self.titulo_cabecalho, border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', border=0, new_x=XPos.RIGHT, new_y=YPos.TOP, align='C')


# ==============================================================================
# 1. GERAR PDF 1: CATÁLOGO DE CURSOS
# ==============================================================================
pdf_cursos = PDF("SkillHub - Catalogo Oficial de Cursos (2026)")
pdf_cursos.add_page()
pdf_cursos.set_font("helvetica", size=11)

conteudo_cursos = """
1. CATALOGO DE CURSOS DISPONIVEIS NA SKILLHUB

A SkillHub oferece atualmente formacoes praticas divididas em 3 grandes trilhas de conhecimento:

A. Trilha de Inteligencia Artificial e Dados
- Formacao Python para Ciencia de Dados: Logica, Pandas, NumPy e visualizacao de dados.
- Formacao Engenharia de Prompts e RAG: Construcao de assistentes virtuais com LangChain, ChromaDB e modelos LLM (Gemini e OpenAI).
- Machine Learning na Pratica: Modelos de regressao, classificacao e agrupamento.

B. Trilha de Desenvolvimento de Software
- Formacao Docker e Containerizacao: Docker, Docker Compose, volumes e deploys em nuvem (OCI/AWS).
- Desenvolvimento Web com Streamlit e FastAPI: Criacao de interfaces modernas e dashboards em Python.
- Engenharia de Software Moderna: Arquitetura limpa, testes automatizados e integracao continua (CI/CD).

C. Trilha de Cloud & DevOps
- Imersao Oracle Cloud Infrastructure (OCI): Provisionamento de maquinas virtuais, VCNs e deploys resilientes.
- Gestao de Infraestrutura como Codigo: Terraform e Ansible para automacao.
"""

for linha in conteudo_cursos.strip().split("\n"):
    pdf_cursos.multi_cell(0, 7, linha, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

pdf_cursos.output("Catalogo_de_Cursos_SkillHub.pdf")
print("✅ PDF 'Catalogo_de_Cursos_SkillHub.pdf' criado com sucesso!")


# ==============================================================================
# 2. GERAR PDF 2: PLANOS E PREÇOS
# ==============================================================================
pdf_planos = PDF("SkillHub - Planos, Precos e Assinaturas (2026)")
pdf_planos.add_page()
pdf_planos.set_font("helvetica", size=11)

conteudo_planos = """
1. PLANOS E OPCOES DE ASSINATURA SKILLHUB

Oferecemos 3 modalidades flexiveis de planos para atender a diferentes necessidades:

A. Plano Basic (R$ 49,90 / mes)
- Acesso a 2 cursos basicos por mes.
- Suporte via comunidade oficial no Discord.
- Emissao de certificado simples de conclusao.

B. Plano Pro (R$ 99,90 / mes ou R$ 999,00 / ano)
- Acesso Ilimitado a TODAS as 3 trilhas de cursos.
- Acesso aos projetos praticos e codigo-fonte no GitHub.
- Suporte prioritario e mentoria mensal em grupo.
- Certificados com validacao de codigo de autenticidade.

C. Plano Enterprise (Sob Consulta / A partir de R$ 499,00 / mes para equipes)
- Acesso ilimitado para multiplos colaboradores.
- Painel corporativo para acompanhamento de progresso da equipe.
- Treinamentos customizados e suporte dedicado 24/7.

2. REGRAS DE RENOVAÇÃO E CANCELAMENTO
- Todas as assinaturas sao renovadas automaticamente ao final do periodo (mensal ou anual).
- O cancelamento pode ser feito a qualquer momento pelo painel do aluno sem multas.
- Garantia de reembolso total de 7 dias apos a primeira assinatura.
"""

for linha in conteudo_planos.strip().split("\n"):
    pdf_planos.multi_cell(0, 7, linha, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

pdf_planos.output("Manual_de_Planos_e_Assinaturas.pdf")
print("✅ PDF 'Manual_de_Planos_e_Assinaturas.pdf' criado com sucesso!")
