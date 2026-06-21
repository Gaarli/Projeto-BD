import os
import sys

# Adiciona a pasta raiz ao path do Python para que ele encontre o módulo backend
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.app import app

if __name__ == "__main__":
    # Define a porta padrão ou pega das variáveis de ambiente
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
    
    print("===================================================")
    print(" Iniciando a Interface Web do EletroReverso...")
    print("===================================================")
    
    # Inicia o servidor Flask importado do app.py
    app.run(host="0.0.0.0", port=port, debug=debug_mode)