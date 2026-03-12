import logging
import re
from langchain_core.messages import SystemMessage

logger = logging.getLogger(__name__)

async def arth_analyst_processor(state: dict) -> dict:
    """Processa requisições do Analista com busca profunda de dados no histórico."""
    
    if state is None:
        state = {}
    
    user_input = str(state.get("user_input", ""))
    content = str(state.get("content", ""))
    last_agent = str(state.get("last_agent", ""))
    messages = list(state.get("messages", []))
    
    logger.info(f"[Analyst] Iniciando processamento profundo de conteúdo.")
    
    # --- BUSCA PROFUNDA DE DADOS ---
    # 1. Tenta pegar do campo 'content' acumulado (Ponte de Ferro)
    rich_content = content if len(content) > 100 else ""
    
    # 2. Se o content estiver fraco, varre TODO o histórico em busca da maior mensagem AI
    if not rich_content:
        # Pega todas as mensagens AI e ordena pela maior (que provavelmente contém os leads/pesquisa)
        ai_messages = [m for m in messages if getattr(m, "type", "") == "ai" and len(str(m.content)) > 200]
        if ai_messages:
            # Pega a mensagem mais longa do histórico
            best_msg = max(ai_messages, key=lambda m: len(str(m.content)))
            rich_content = str(best_msg.content)
            logger.info(f"[Analyst] 📥 Dados recuperados do histórico profundo ({len(rich_content)} chars)")

    # 3. Fallback final
    if not rich_content:
        rich_content = f"Relatório estratégico baseado na solicitação: {user_input}"
        logger.warning(f"[Analyst] ⚠️ Nenhum dado robusto encontrado no histórico.")

    logger.info(f"[Analyst] Conteúdo consolidado para o PDF: {len(rich_content)} caracteres")
    
    # --- INSTRUÇÃO DE REDAÇÃO EXECUTIVA ---
    instruction = (
        "🚨 MISSÃO CRÍTICA: VOCÊ É O REDATOR-CHEFE DA ARTIFICIALL.\n"
        "Sua única tarefa agora é transformar os dados abaixo em um PDF profissional e elegante.\n\n"
        "1. NÃO RESUMA. Use todos os nomes, CEOs e detalhes encontrados na pesquisa.\n"
        "2. FORMATAÇÃO: Use # para títulos, ## para subtítulos e - para listas.\n"
        "3. AÇÃO IMEDIATA: Chame a ferramenta 'generate_pdf' agora.\n"
        "4. O campo 'content' da ferramenta DEVE conter o texto completo que você redigiu.\n"
        "5. Finalize com a tag <SEND_FILE:nome_do_arquivo>."
    )
    
    full_instruction = f"{instruction}\n\n--- DADOS PARA O RELATÓRIO ---\n{rich_content}\n--- FIM DOS DADOS ---"

    # Injeta a instrução no topo para o modelo não ignorar
    new_messages = messages + [SystemMessage(content=full_instruction)]
    
    return {**state, "messages": new_messages, "content": rich_content}
