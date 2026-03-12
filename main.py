import os
import uvicorn
import sys

# Adiciona o diretório raiz ao path para encontrar o app.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    # Executa o app que está na raiz
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
