import requests
import os
from config import settings

def set_webhook(url):
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        print("❌ Erro: TELEGRAM_BOT_TOKEN não configurado no .env ou no ambiente.")
        return

    # O endpoint do webhook é definido no app.py
    webhook_url = f"{url}/api/v1/telegram/webhook"
    
    api_url = f"https://api.telegram.org/bot{token}/setWebhook"
    payload = {"url": webhook_url}
    
    print(f"📡 Configurando Webhook para: {webhook_url}")
    response = requests.post(api_url, json=payload)
    
    if response.status_code == 200:
        print("✅ Webhook configurado com sucesso no Telegram!")
        print(response.json())
    else:
        print(f"❌ Falha ao configurar Webhook: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python setup_webhooks.py <URL_DO_RAILWAY>")
        print("Exemplo: python setup_webhooks.py https://seu-app.up.railway.app")
    else:
        set_webhook(sys.argv[1])
