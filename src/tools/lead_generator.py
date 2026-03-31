import subprocess
import os
import logging
import json
import asyncio
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from src.config import settings

logger = logging.getLogger(__name__)

class LeadGenSchema(BaseModel):
    query: str = Field(description="O nicho e cidade para busca (ex: 'Padarias em Curitiba')")
    source: str = Field(description="A fonte de dados: 'maps', 'linkedin' ou 'apify'", default="maps")

@tool(args_schema=LeadGenSchema)
async def run_lead_generator(query: str, source: str = "maps") -> str:
    """
    Aciona o motor de extração de leads profissional (Node.js).
    Retorna um resumo da operação e envia os leads para o Supabase.
    """
    logger.info(f"🚀 [LEAD-GEN] Iniciando motor para: '{query}' via {source}")
    
    # Caminho do script principal do Gerador de Leads (integrado)
    script_path = os.path.join("src", "tools", "lead_generator_engine", "index.js")
    
    if not os.path.exists(script_path):
        return "Erro: Motor de geração de leads não encontrado no servidor."

    try:
        # Executa o processo Node.js de forma assíncrona
        process = await asyncio.create_subprocess_exec(
            "node", script_path, query, source,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()
        
        output = stdout.decode(errors='replace')
        error_output = stderr.decode(errors='replace')

        if process.returncode != 0:
            logger.error(f"[LEAD-GEN] Falha no motor Node.js: {error_output}")
            return f"Falha na extração: {error_output}"

        # Tenta extrair o JSON de resumo se o script o emitiu
        summary = "Extração concluída com sucesso."
        if "__SUMMARY_JSON__" in output:
            try:
                json_str = output.split("__SUMMARY_JSON__")[-1].strip()
                data = json.loads(json_str)
                summary = (
                    f"✅ Sucesso! {data.get('extraidos', 0)} leads encontrados, "
                    f"{data.get('enriquecidos', 0)} enriquecidos e enviados ao Dashboard."
                )
            except: pass

        logger.info(f"[LEAD-GEN] Finalizado: {summary}")
        return summary

    except Exception as e:
        logger.error(f"[LEAD-GEN] Erro ao executar subprocesso: {e}")
        return f"Erro técnico no motor de leads: {str(e)}"
