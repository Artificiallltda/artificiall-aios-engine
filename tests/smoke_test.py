import os
import sys
import pytest
from config import settings

def test_environment_variables():
    """Verifica se as variÃ¡veis mÃ­nimas para o Squad de Growth existem"""
    # Nota: Em teste, verificamos se as chaves estÃ£o no objeto settings
    assert hasattr(settings, "OPENAI_API_KEY")
    assert hasattr(settings, "SUPABASE_URL")
    assert settings.APP_NAME == "Artificiall Growth Engine"

def test_agents_directories():
    """Verifica se a pasta de agentes do AIOS existe e contÃ©m arquivos"""
    agents_path = settings.SQUAD_PATH
    assert os.path.exists(agents_path)
    agents_files = [f for f in os.listdir(agents_path) if f.endswith(".md")]
    assert len(agents_files) >= 10, f"Esperado 10+ agentes, encontrado {len(agents_files)}"

def test_api_trigger_endpoint():
    """Verifica se o roteador de mensagens foi carregado"""
    from router.message_handler import router
    assert router is not None
    assert any(route.path == "/trigger" for route in router.routes)

if __name__ == "__main__":
    print("🚀 Rodando Auditoria Sistêmica...")
