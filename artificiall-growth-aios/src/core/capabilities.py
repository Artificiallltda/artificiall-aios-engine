from typing import Dict, List

AGENT_CAPABILITIES: Dict[str, Dict] = {
    "growth_executor": {
        "can_generate": ["image", "jpg", "png", "jpeg", "pdf", "docx", "pptx"],
        "tools": ["image_generator", "doc_generator", "pptx_generator"],
        "can_search": False,
        "description": "Executa tarefas práticas, gera imagens e documentos de marketing."
    },
    "growth_analyst": {
        "can_generate": ["excel", "xlsx", "xls", "pdf", "docx"],
        "tools": ["data_analyst", "excel_generator", "doc_generator"],
        "can_search": False,
        "description": "Analisa dados de mercado e leads, gera planilhas e relatórios de performance."
    },
    "growth_researcher": {
        "can_generate": [],
        "tools": ["web_search", "web_reader"],
        "can_search": True,
        "description": "Pesquisa informações GEO e tendências de mercado."
    },
    "growth_planner": {
        "can_generate": [],
        "tools": ["scheduler_tools"],
        "can_search": False,
        "description": "Planeja estratégias de Growth e campanhas AEO."
    },
    "growth_sdr": {
        "can_generate": [],
        "tools": ["web_search"],
        "can_search": True,
        "description": "Prospecção ativa e busca de leads (CEOs/CFOs)."
    },
    "growth_closer": {
        "can_generate": ["pdf", "docx"],
        "tools": ["doc_generator"],
        "can_search": False,
        "description": "Fechamento de propostas e negociação comercial."
    },
    "growth_commerce": {
        "can_generate": [],
        "tools": ["database_tools"],
        "can_search": False,
        "description": "Gerenciamento de fluxos de venda e transações."
    },
    "growth_auditor": {
        "can_generate": ["pdf"],
        "tools": ["web_search", "doc_generator"],
        "can_search": True,
        "description": "Auditoria de qualidade, E-E-A-T e autoridade."
    },
    "growth_creative": {
        "can_generate": ["image", "pptx"],
        "tools": ["image_generator", "pptx_generator"],
        "can_search": False,
        "description": "Direção criativa e geração de decks visuais."
    },
    "growth_manager": {
        "can_generate": ["excel"],
        "tools": ["scheduler_tools", "excel_generator"],
        "can_search": False,
        "description": "Gestão de campanhas e cronogramas de Growth."
    }
}

def get_agent_for_file_type(file_type: str) -> str:
    """Retorna o agente correto para gerar um tipo de arquivo."""
    file_type = file_type.lower().replace(".", "")
    for agent, caps in AGENT_CAPABILITIES.items():
        if file_type in caps.get("can_generate", []):
            return agent
    return "growth_analyst"  # fallback padrão

def can_agent_generate(agent: str, file_type: str) -> bool:
    """Verifica se um agente específico pode gerar um tipo de arquivo."""
    caps = AGENT_CAPABILITIES.get(agent, {})
    return file_type in caps.get("can_generate", [])
