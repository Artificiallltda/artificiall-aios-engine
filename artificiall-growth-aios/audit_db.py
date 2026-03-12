import psycopg
import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("SUPABASE_DATABASE_URL")

def audit_supabase():
    if not db_url:
        print("❌ SUPABASE_DATABASE_URL não configurada.")
        return

    try:
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                # 1. Checa KPIs
                cur.execute("SELECT count(*) FROM agent_kpis")
                kpi_count = cur.fetchone()[0]
                print(f"📊 Registros em agent_kpis: {kpi_count}")

                # 2. Checa Leads
                cur.execute("SELECT count(*) FROM leads")
                leads_count = cur.fetchone()[0]
                print(f"🕵️‍♂️ Registros em leads: {leads_count}")

                # 3. Checa Logs
                cur.execute("SELECT count(*) FROM agent_logs")
                logs_count = cur.fetchone()[0]
                print(f"📝 Registros em agent_logs: {logs_count}")

                if leads_count > 0:
                    cur.execute("SELECT company_name, created_at FROM leads ORDER BY created_at DESC LIMIT 3")
                    print("\n--- Últimos Leads ---")
                    for row in cur.fetchall():
                        print(f"- {row[0]} ({row[1]})")

    except Exception as e:
        print(f"❌ Erro na auditoria: {e}")

if __name__ == "__main__":
    audit_supabase()
