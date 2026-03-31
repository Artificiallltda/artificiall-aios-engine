import psycopg
import os
from dotenv import load_dotenv

# Carrega variáveis
load_dotenv()
db_url = os.getenv("SUPABASE_DATABASE_URL")

if not db_url:
    print("❌ Erro: SUPABASE_DATABASE_URL não encontrada no .env")
    exit(1)

sql_create = """
CREATE TABLE IF NOT EXISTS agent_kpis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    citation_share FLOAT DEFAULT 0.0,
    sentiment_positivity FLOAT DEFAULT 0.0,
    identified_gaps INT DEFAULT 0,
    model_coverage JSONB DEFAULT '{"chatgpt": 0, "claude": 0, "gemini": 0, "perplexity": 0}',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
"""

sql_init = """
INSERT INTO agent_kpis (citation_share, sentiment_positivity, identified_gaps, model_coverage)
SELECT 68.4, 94.2, 14, '{"chatgpt": 82, "claude": 76, "gemini": 45, "perplexity": 91}'::jsonb
WHERE NOT EXISTS (SELECT 1 FROM agent_kpis);
"""

try:
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql_create)
            cur.execute(sql_init)
            conn.commit()
            print("✅ Tabela agent_kpis criada e populada com dados iniciais!")
except Exception as e:
    print(f"❌ Erro ao acessar o banco: {e}")
