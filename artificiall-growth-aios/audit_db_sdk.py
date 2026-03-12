import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def audit_supabase():
    if not url or not key:
        print("❌ Chaves SUPABASE_URL ou SERVICE_ROLE_KEY não configuradas.")
        return

    try:
        supabase = create_client(url, key)
        
        # 1. Checa KPIs
        kpis = supabase.table('agent_kpis').select('count', count='exact').execute()
        print(f"📊 Registros em agent_kpis: {kpis.count}")

        # 2. Checa Leads
        leads = supabase.table('leads').select('count', count='exact').execute()
        print(f"🕵️‍♂️ Registros em leads: {leads.count}")

        if leads.count > 0:
            last_leads = supabase.table('leads').select('company_name, created_at').order('created_at', desc=True).limit(3).execute()
            print("\n--- Últimos Leads ---")
            for lead in last_leads.data:
                print(f"- {lead['company_name']} ({lead['created_at']})")

    except Exception as e:
        print(f"❌ Erro na auditoria: {e}")

if __name__ == "__main__":
    audit_supabase()
